import json
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import SUPPORTED_LANGUAGES, settings
from app.database import Base, SessionLocal, engine
from app.models.alert import Alert, CommunityInsight
from app.routers import (
    advanced, alerts, analytics, expenses, farmers, features,
    proactive, twilio_voice, unique, web_voice, whatsapp,
)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("kisanvaani")

# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])


def _cleanup_old_audio():
    """Remove audio files older than AUDIO_CACHE_TTL_HOURS."""
    audio_dir = Path(settings.AUDIO_DIR)
    if not audio_dir.exists():
        return
    ttl_seconds = settings.AUDIO_CACHE_TTL_HOURS * 3600
    now = time.time()
    removed = 0
    for f in audio_dir.iterdir():
        if f.is_file() and (now - f.stat().st_mtime) > ttl_seconds:
            f.unlink()
            removed += 1
    if removed:
        logger.info(f"Audio cleanup: removed {removed} expired files")


def _seed_demo_data():
    """Seed alerts and community insights for demo purposes."""
    db = SessionLocal()
    try:
        if db.query(Alert).count() == 0:
            demo_alerts = [
                Alert(alert_type="weather", severity="warning", title="Heavy Rainfall Expected — Maharashtra",
                      message="IMD predicts heavy rainfall (100mm+) in Vidarbha region March 31 - April 2. Delay pesticide spraying. Ensure drainage channels are clear. Harvest mature crops immediately.",
                      country="IN", region="Maharashtra", affected_crops=json.dumps(["Cotton", "Soybean"]), source="IMD"),
                Alert(alert_type="pest_outbreak", severity="critical", title="Fall Armyworm Alert — Western Kenya",
                      message="Fall armyworm infestation reported in Kakamega and Bungoma counties. Inspect maize fields daily. Apply neem oil spray (5ml/liter) as preventive measure. Report sightings to county extension officer.",
                      country="KE", region="Western Kenya", affected_crops=json.dumps(["Maize"]), source="County Agriculture Office"),
                Alert(alert_type="price_spike", severity="info", title="Tomato Prices Rising — Karnataka",
                      message="Tomato mandi prices up 40% this week (Rs 3,100/quintal). Good time to sell if harvest is ready. Prices expected to stabilize in 2 weeks.",
                      country="IN", region="Karnataka", affected_crops=json.dumps(["Tomato"]), source="AgMarkNet"),
                Alert(alert_type="scheme_deadline", severity="warning", title="PM-KISAN Registration Deadline",
                      message="Last date for PM-KISAN new registration is April 15, 2026. Visit your nearest CSC center with Aadhaar and land documents. Existing beneficiaries check payment status at pmkisan.gov.in.",
                      country="IN", region=None, affected_crops=None, source="Govt of India"),
                Alert(alert_type="weather", severity="critical", title="Drought Warning — Northern Nigeria",
                      message="Below-normal rainfall predicted for Kano, Kaduna, and Katsina states. Plant drought-resistant varieties. Mulch around crops to retain moisture. Contact state ADP for emergency seed distribution.",
                      country="NG", region="Northern Nigeria", affected_crops=json.dumps(["Maize", "Sorghum", "Millet"]), source="NiMet"),
            ]
            db.add_all(demo_alerts)

        if db.query(CommunityInsight).count() == 0:
            demo_insights = [
                CommunityInsight(region="Vidarbha", country="IN", topic="Cotton Bollworm", affected_crop="Cotton",
                                 farmer_count=23, trending=1,
                                 ai_summary="23 farmers in Vidarbha reported bollworm infestation this week. Neem oil spray and pheromone traps recommended. Consider Bt cotton for next season."),
                CommunityInsight(region="Telangana", country="IN", topic="Rice Blast Disease", affected_crop="Rice",
                                 farmer_count=15, trending=1,
                                 ai_summary="Rice blast spreading in Telangana due to recent humid weather. Tricyclazole spray recommended. Avoid excess nitrogen fertilizer."),
                CommunityInsight(region="Western Kenya", country="KE", topic="Fall Armyworm", affected_crop="Maize",
                                 farmer_count=47, trending=1,
                                 ai_summary="Major fall armyworm outbreak in Western Kenya. 47 farmers affected. Early morning hand-picking + neem spray most effective for small plots."),
                CommunityInsight(region="Kano", country="NG", topic="Late Planting Concerns", affected_crop="Maize",
                                 farmer_count=12, trending=0,
                                 ai_summary="12 farmers worried about delayed rains affecting planting schedules. Short-duration maize varieties (SAMMAZ 15) recommended."),
                CommunityInsight(region="Karnataka", country="IN", topic="Tomato Leaf Curl Virus", affected_crop="Tomato",
                                 farmer_count=31, trending=1,
                                 ai_summary="Tomato leaf curl virus spreading via whitefly. 31 farmers affected. Remove infected plants. Spray imidacloprid for whitefly control. Use virus-resistant varieties."),
            ]
            db.add_all(demo_insights)

        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting KisanVaani v2.1...")
    Base.metadata.create_all(bind=engine)
    _seed_demo_data()
    _cleanup_old_audio()
    # Seed price history for price prediction
    from app.services.price_predictor import seed_price_history
    db = SessionLocal()
    try:
        seed_price_history(db)
    finally:
        db.close()
    logger.info(f"Mode: {'MOCK' if settings.MOCK_MODE else 'PRODUCTION'} | Model: {settings.CLAUDE_MODEL}")
    yield
    logger.info("Shutting down KisanVaani")


app = FastAPI(
    title="KisanVaani",
    description="Voice-First AI Farm Advisor — Multi-country, with Farmer Memory, Photo Diagnosis, Proactive Alerts, and Expense Tracking",
    version="2.1.0",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    if request.url.path.startswith("/api/"):
        logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration:.2f}s)")
    return response


app.include_router(web_voice.router)
app.include_router(twilio_voice.router)
app.include_router(whatsapp.router)
app.include_router(analytics.router)
app.include_router(farmers.router)
app.include_router(alerts.router)
app.include_router(expenses.router)
app.include_router(features.router)
app.include_router(advanced.router)
app.include_router(proactive.router)
app.include_router(unique.router)


@app.get("/api/health")
def health():
    """Enhanced health check with database and external service status."""
    db_ok = False
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db_ok = True
        db.close()
    except Exception:
        pass

    return {
        "status": "ok" if db_ok else "degraded",
        "service": "KisanVaani",
        "version": "2.1.0",
        "mock_mode": settings.MOCK_MODE,
        "database": "connected" if db_ok else "error",
        "ai_configured": bool(settings.ANTHROPIC_API_KEY),
        "twilio_configured": bool(settings.TWILIO_ACCOUNT_SID),
    }


@app.get("/api/languages")
def get_languages():
    return {
        code: {"name": info["name"], "native_name": info["native_name"]}
        for code, info in SUPPORTED_LANGUAGES.items()
    }


@app.get("/api/countries")
def get_countries():
    from app.services.farming_knowledge import get_countries
    countries = get_countries()
    return {
        code: {"name": data["name"], "languages": data["languages"], "currency": data["currency"]}
        for code, data in countries.items()
    }


# Serve frontend static files in production (when built with npm run build)
# Uses middleware approach to avoid catch-all route conflicting with API routes
import os
from starlette.responses import FileResponse as _StaticFileResponse, Response as _StaticResponse

_static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.isdir(_static_dir):
    from fastapi.staticfiles import StaticFiles
    app.mount("/assets", StaticFiles(directory=os.path.join(_static_dir, "assets")), name="static-assets")

    @app.middleware("http")
    async def serve_spa(request: Request, call_next):
        """Serve frontend SPA for non-API routes. API routes pass through to routers."""
        response = await call_next(request)

        # If API returned 404 for a non-API path, serve index.html (SPA routing)
        path = request.url.path
        if response.status_code == 404 and not path.startswith("/api/"):
            # Try serving a static file first
            file_path = os.path.join(_static_dir, path.lstrip("/"))
            if os.path.isfile(file_path):
                return _StaticFileResponse(file_path)
            # Fallback to index.html for SPA routes
            index_path = os.path.join(_static_dir, "index.html")
            if os.path.isfile(index_path):
                return _StaticFileResponse(index_path)

        return response
