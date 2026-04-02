"""Unique feature routes: Soil Test OCR, Crop Insurance Auto-Claims, SMS Fallback."""
import base64
import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.insurance_service import generate_claim_package, get_insurance_schemes
from app.services.sms_service import process_sms, send_sms
from app.services.soil_ocr_service import analyze_soil_report

logger = logging.getLogger("kisanvaani.unique")
router = APIRouter(prefix="/api", tags=["unique"])


# ────────────────────────────────
# SOIL TEST REPORT OCR
# ────────────────────────────────

@router.post("/soil/analyze")
async def analyze_soil_test(
    photo: UploadFile = File(...),
    language: str = Form("en"),
    crop: Optional[str] = Form(None),
):
    """Upload a soil test report card image for AI analysis.

    Returns extracted values (pH, N, P, K, etc.), interpretation,
    and crop-specific fertilizer recommendations.
    """
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if photo.content_type and photo.content_type not in allowed:
        raise HTTPException(400, "Unsupported image type")

    photo_bytes = await photo.read()
    if len(photo_bytes) > 10 * 1024 * 1024:
        raise HTTPException(400, "Image too large (max 10MB)")

    image_b64 = base64.b64encode(photo_bytes).decode("utf-8")
    content_type = photo.content_type or "image/jpeg"

    logger.info(f"Soil OCR: {len(photo_bytes)//1024}KB, lang={language}, crop={crop}")

    result = await analyze_soil_report(
        image_data=image_b64,
        image_media_type=content_type,
        language=language,
        crop=crop,
    )
    return result


class SoilManualEntry(BaseModel):
    """Manual soil test values for interpretation (without image upload)."""
    ph: Optional[float] = None
    nitrogen: Optional[float] = None
    phosphorus: Optional[float] = None
    potassium: Optional[float] = None
    organic_carbon: Optional[float] = None
    soil_type: Optional[str] = None
    crop: Optional[str] = None


@router.post("/soil/interpret")
async def interpret_soil_values(data: SoilManualEntry):
    """Interpret manually entered soil test values.
    For farmers who can read values but need interpretation.
    """
    issues = []
    recommendations = []
    health = "good"

    # pH analysis
    if data.ph is not None:
        if data.ph < 5.5:
            issues.append(f"pH {data.ph} is too acidic. Apply lime 2-4 quintals/acre.")
            health = "poor"
        elif data.ph > 8.5:
            issues.append(f"pH {data.ph} is too alkaline. Apply gypsum 2-3 quintals/acre.")
            health = "poor"
        elif 6.0 <= data.ph <= 7.5:
            recommendations.append(f"pH {data.ph} is ideal for most crops.")
        else:
            issues.append(f"pH {data.ph} is slightly {'acidic' if data.ph < 6.0 else 'alkaline'}.")
            health = "moderate"

    # Nitrogen
    if data.nitrogen is not None:
        if data.nitrogen < 150:
            issues.append(f"Nitrogen LOW ({data.nitrogen} kg/ha). Apply Urea 50-75 kg/acre.")
            health = "poor" if health != "poor" else health
        elif data.nitrogen > 300:
            recommendations.append(f"Nitrogen adequate ({data.nitrogen} kg/ha).")
        else:
            recommendations.append(f"Nitrogen moderate ({data.nitrogen} kg/ha). Apply Urea 25 kg/acre.")

    # Phosphorus
    if data.phosphorus is not None:
        if data.phosphorus < 15:
            issues.append(f"Phosphorus LOW ({data.phosphorus} kg/ha). Apply DAP 50 kg/acre at sowing.")
            health = "poor" if health != "poor" else health
        elif data.phosphorus > 30:
            recommendations.append(f"Phosphorus adequate ({data.phosphorus} kg/ha).")

    # Potassium
    if data.potassium is not None:
        if data.potassium < 120:
            issues.append(f"Potassium LOW ({data.potassium} kg/ha). Apply MOP (Muriate of Potash) 25 kg/acre.")
            health = "poor" if health != "poor" else health
        elif data.potassium > 200:
            recommendations.append(f"Potassium good ({data.potassium} kg/ha).")

    # Organic Carbon
    if data.organic_carbon is not None:
        if data.organic_carbon < 0.5:
            issues.append(f"Organic Carbon very LOW ({data.organic_carbon}%). Apply FYM 2-3 tonnes/acre + green manure.")
            health = "poor"
        elif data.organic_carbon < 0.75:
            issues.append(f"Organic Carbon low ({data.organic_carbon}%). Apply compost 1-2 tonnes/acre.")

    # Crop suitability
    suitability = []
    if data.ph is not None:
        if 6.0 <= data.ph <= 7.5:
            suitability = ["Wheat", "Rice", "Tomato", "Cotton", "Soybean", "Maize"]
        elif data.ph < 6.0:
            suitability = ["Rice", "Tea", "Potato", "Blueberry"]
        else:
            suitability = ["Barley", "Cotton", "Sugarbeet"]

    return {
        "health": health,
        "issues": issues,
        "recommendations": recommendations,
        "crop_suitability": suitability,
        "input_values": data.model_dump(exclude_none=True),
    }


# ────────────────────────────────
# CROP INSURANCE AUTO-CLAIMS
# ────────────────────────────────

class InsuranceClaimRequest(BaseModel):
    farmer_id: int
    crop: str
    damage_type: str  # drought, flood, pest, disease, hail, other
    damage_description: str
    country: str = "IN"


@router.post("/insurance/claim")
async def generate_insurance_claim(body: InsuranceClaimRequest, db: Session = Depends(get_db)):
    """Generate a complete insurance claim package from farmer data.

    Auto-collects evidence from crop diary, expenses, satellite data,
    and generates all required documentation guidance.
    """
    result = generate_claim_package(
        db, body.farmer_id, body.crop, body.damage_type,
        body.damage_description, body.country,
    )
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result


@router.get("/insurance/schemes/{country}")
async def list_insurance_schemes(country: str):
    """List available crop insurance schemes for a country."""
    schemes = get_insurance_schemes(country)
    if not schemes:
        return {"message": f"No insurance schemes found for {country}", "schemes": []}
    return {"country": country, "schemes": schemes}


# ────────────────────────────────
# SMS FALLBACK
# ────────────────────────────────

@router.post("/sms/webhook")
async def sms_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle incoming SMS from Twilio.

    Supports commands (HELP, REGISTER, PRICE, WEATHER, EXPENSE, SCHEME)
    and free-form farming questions processed through AI.
    """
    form = await request.form()
    body = form.get("Body", "").strip()
    sender = form.get("From", "")

    logger.info(f"SMS from {sender[:6]}***: {body[:50]}...")

    response_text = await process_sms(db, sender, body)

    # Return TwiML
    safe = response_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{safe}</Message>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


class SMSSendRequest(BaseModel):
    to: str
    message: str


@router.post("/sms/send")
async def send_sms_message(body: SMSSendRequest):
    """Send outbound SMS to a farmer."""
    result = await send_sms(body.to, body.message)
    return result


@router.get("/sms/commands")
async def sms_commands():
    """List available SMS commands."""
    from app.services.sms_service import SMS_COMMANDS
    return {"commands": SMS_COMMANDS}
