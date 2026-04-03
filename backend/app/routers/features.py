"""All new feature routes: weather, crop diary, KVK, yield, loans, pests, report, onboarding."""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.farmer import FarmerProfile
from app.services.extra_services import (
    add_diary_entry, check_loan_eligibility, find_nearest_kvk, generate_farmer_report,
    get_all_pests, get_diary_entries, get_pending_reminders, get_pest_info,
    get_upcoming_reminders, predict_yield,
)
from app.services.weather_service import get_weather

router = APIRouter(prefix="/api", tags=["features"])


# --- WEATHER ---
@router.get("/weather/{location}")
async def weather_forecast(location: str, days: int = 3):
    result = await get_weather(location, days)
    # Return error as 200 with error field so frontend can display it
    # (404 causes frontend to show nothing)
    return result


# --- KVK LOCATOR ---
@router.get("/kvk/{country}/{region}")
def kvk_locator(country: str, region: str, district: Optional[str] = None):
    results = find_nearest_kvk(country, region, district)
    if not results:
        return {"message": f"No extension centers found for {region}, {country}", "results": []}
    return {"results": results}


# --- YIELD PREDICTOR ---
class YieldRequest(BaseModel):
    country: str = "IN"
    crop: str
    land_acres: float = 1.0
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None


@router.post("/yield/predict")
def yield_predict(data: YieldRequest):
    result = predict_yield(data.country, data.crop, data.land_acres, data.soil_type, data.irrigation_type)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# --- LOAN ELIGIBILITY ---
@router.get("/loans/{country}")
def loan_eligibility(country: str, land_acres: float = 0):
    return check_loan_eligibility(country, land_acres)


# --- PEST GALLERY ---
@router.get("/pests")
def list_pests():
    return get_all_pests()


@router.get("/pests/{pest_name}")
def pest_detail(pest_name: str):
    result = get_pest_info(pest_name)
    if not result:
        raise HTTPException(status_code=404, detail=f"Pest '{pest_name}' not found")
    return result


# --- CROP DIARY ---
class DiaryEntry(BaseModel):
    farmer_id: int
    crop: str
    activity: str  # planted, irrigated, fertilized, sprayed, harvested, weeded, sold
    details: str = ""
    quantity: str = ""
    date: str = ""  # YYYY-MM-DD, defaults to today


@router.post("/diary")
def add_diary(data: DiaryEntry, db: Session = Depends(get_db)):
    entry = add_diary_entry(db, data.farmer_id, data.crop, data.activity,
                            data.details, data.quantity, data.date or "")
    return {
        "id": entry.id, "crop": entry.crop, "activity": entry.activity,
        "details": entry.details, "date": entry.date_recorded,
    }


@router.get("/diary/{farmer_id}")
def get_diary(farmer_id: int, db: Session = Depends(get_db)):
    entries = get_diary_entries(db, farmer_id)
    return [
        {"id": e.id, "crop": e.crop, "activity": e.activity,
         "details": e.details, "quantity": e.quantity, "date": e.date_recorded}
        for e in entries
    ]


@router.get("/reminders/{farmer_id}")
def get_reminders(farmer_id: int, days: int = 14, db: Session = Depends(get_db)):
    pending = get_pending_reminders(db, farmer_id)
    upcoming = get_upcoming_reminders(db, farmer_id, days)

    # Deduplicate
    seen = set()
    all_reminders = []
    for r in pending + upcoming:
        if r.id not in seen:
            seen.add(r.id)
            all_reminders.append({
                "id": r.id, "crop": r.crop, "type": r.reminder_type,
                "message": r.message, "due_date": r.due_date,
                "overdue": r.due_date < str(__import__("datetime").date.today()),
            })
    return all_reminders


# --- FARMER REPORT ---
@router.get("/report/{farmer_id}")
def farmer_report(farmer_id: int, db: Session = Depends(get_db)):
    farmer = db.query(FarmerProfile).filter(FarmerProfile.id == farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")

    farmer_data = {
        "name": farmer.name, "region": farmer.region, "district": farmer.district,
        "village": farmer.village, "country": farmer.country,
        "land_size_acres": farmer.land_size_acres,
        "soil_type": farmer.soil_type, "irrigation_type": farmer.irrigation_type,
        "crops": json.loads(farmer.crops) if farmer.crops else [],
    }
    report = generate_farmer_report(db, farmer_id, farmer_data)
    return {"farmer_id": farmer_id, "report": report}


# --- FARMER ONBOARDING ---
class OnboardingData(BaseModel):
    name: str
    preferred_language: str = "hi"
    country: str = "IN"
    region: Optional[str] = None
    district: Optional[str] = None
    village: Optional[str] = None
    land_size_acres: Optional[float] = None
    crops: list[str] = []
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None


@router.post("/onboard")
def onboard_farmer(data: OnboardingData, db: Session = Depends(get_db)):
    """Quick onboarding — creates farmer profile and returns welcome + first tips."""
    farmer = FarmerProfile(
        name=data.name,
        preferred_language=data.preferred_language,
        country=data.country,
        region=data.region,
        district=data.district,
        village=data.village,
        land_size_acres=data.land_size_acres,
        crops=json.dumps(data.crops),
        soil_type=data.soil_type,
        irrigation_type=data.irrigation_type,
    )
    db.add(farmer)
    db.commit()
    db.refresh(farmer)

    # Generate initial tips
    tips = []
    if data.crops:
        tips.append(f"For your {', '.join(data.crops)}: ask me about planting schedule, pest prevention, and market prices.")
    if data.country == "IN":
        tips.append("Check your PM-KISAN eligibility — ask me 'PM KISAN ke liye apply kaise karein?'")
    if data.land_size_acres and data.land_size_acres < 5:
        tips.append("As a small farmer, you may qualify for special government schemes. Ask me about them!")
    tips.append("You can send me a photo of any crop problem for instant diagnosis.")
    tips.append("Say your expenses out loud and I'll track them for you automatically.")

    return {
        "farmer_id": farmer.id,
        "welcome_message": f"Welcome to KisanVaani, {data.name}! Your profile is set up.",
        "tips": tips,
    }
