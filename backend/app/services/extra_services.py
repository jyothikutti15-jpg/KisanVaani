"""All extra services: KVK locator, yield predictor, loan calculator, pest gallery, onboarding."""
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.models.crop_diary import CropDiaryEntry, CropReminder

DATA_DIR = Path(__file__).parent.parent / "data"


def _load(filename: str) -> dict | list:
    try:
        with open(DATA_DIR / filename, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# --- KVK LOCATOR ---
def find_nearest_kvk(country: str, region: str, district: Optional[str] = None) -> list[dict]:
    directory = _load("kvk_directory.json")
    country_data = directory.get(country, {})

    results = []
    for reg_name, kvks in country_data.items():
        if region.lower() in reg_name.lower() or reg_name.lower() in region.lower():
            results.extend(kvks)

    # Also search by district
    if district and not results:
        for reg_name, kvks in country_data.items():
            for kvk in kvks:
                if district.lower() in kvk.get("district", "").lower():
                    results.append(kvk)

    return results[:5]


# --- YIELD PREDICTOR ---
def predict_yield(country: str, crop: str, land_acres: float = 1.0,
                  soil_type: Optional[str] = None, irrigation: Optional[str] = None) -> dict:
    yield_data = _load("yield_data.json")
    country_data = yield_data.get(country, {})

    # Find crop (case-insensitive)
    crop_data = None
    for c, data in country_data.items():
        if c.lower() == crop.lower():
            crop_data = data
            break

    if not crop_data:
        return {"error": f"No yield data for {crop} in {country}"}

    base_yield = crop_data["avg_yield_quintal_per_acre"]
    low, high = crop_data["range"]

    # Adjust for soil and irrigation
    multiplier = 1.0
    notes = []
    if irrigation and irrigation.lower() in ("drip", "sprinkler"):
        multiplier += 0.25
        notes.append("Drip/sprinkler irrigation: +25%")
    elif irrigation and irrigation.lower() != "rainfed":
        multiplier += 0.15
        notes.append("Irrigation available: +15%")

    if soil_type and soil_type.lower() in ("black", "alluvial"):
        multiplier += 0.10
        notes.append(f"{soil_type} soil: +10%")

    predicted = round(base_yield * multiplier, 1)
    total = round(predicted * land_acres, 1)

    return {
        "crop": crop,
        "predicted_yield_per_acre": predicted,
        "total_yield": total,
        "land_acres": land_acres,
        "unit": "quintals",
        "range": [round(low * land_acres, 1), round(high * land_acres * multiplier, 1)],
        "season": crop_data["season"],
        "factors": crop_data["factors"],
        "adjustments": notes,
    }


# --- LOAN CALCULATOR ---
def check_loan_eligibility(country: str, land_acres: float = 0) -> list[dict]:
    schemes = _load("loan_schemes.json")
    country_schemes = schemes.get(country, [])

    results = []
    for scheme in country_schemes:
        eligible = True
        reason = "Eligible based on farmer status"

        # Basic eligibility check
        if land_acres <= 0 and "land" in scheme.get("eligibility", "").lower():
            eligible = False
            reason = "Land ownership required"

        results.append({
            "name": scheme["name"],
            "eligible": eligible,
            "reason": reason,
            "max_amount": scheme["max_amount"],
            "interest_rate": scheme["interest_rate"],
            "documents": scheme["documents"],
            "where_to_apply": scheme["where_to_apply"],
            "repayment": scheme["repayment"],
        })

    return results


# --- PEST GALLERY ---
def get_pest_info(pest_name: str) -> Optional[dict]:
    gallery = _load("pest_gallery.json")
    pest_lower = pest_name.lower().replace(" ", "_")

    # Direct match
    if pest_lower in gallery:
        return gallery[pest_lower]

    # Fuzzy match
    for key, data in gallery.items():
        if pest_lower in key or key in pest_lower:
            return data
        if pest_lower in data.get("name", "").lower():
            return data

    return None


def get_all_pests() -> list[dict]:
    gallery = _load("pest_gallery.json")
    return [{"id": k, **v} for k, v in gallery.items()]


# --- CROP DIARY ---
def add_diary_entry(db: Session, farmer_id: int, crop: str, activity: str,
                    details: str = "", quantity: str = "", planting_date: str = "") -> CropDiaryEntry:
    today = date.today().isoformat()
    entry = CropDiaryEntry(
        farmer_id=farmer_id,
        crop=crop,
        activity=activity,
        details=details,
        quantity=quantity,
        date_recorded=planting_date or today,
    )
    db.add(entry)

    # Auto-generate reminders if this is a planting event
    if activity.lower() in ("planted", "sowed", "sowing"):
        _generate_crop_reminders(db, farmer_id, crop, planting_date or today)

    db.commit()
    db.refresh(entry)
    return entry


def _generate_crop_reminders(db: Session, farmer_id: int, crop: str, planting_date: str):
    """Generate standard reminders based on crop type."""
    base = datetime.strptime(planting_date, "%Y-%m-%d")

    reminders_template = {
        "wheat": [
            (21, "irrigation", "First irrigation due — crown root initiation stage. Apply light irrigation."),
            (42, "fertilizer", "Second dose of urea (25 kg/acre) — tillering stage."),
            (60, "pest_check", "Check for yellow rust and aphids. Scout early morning."),
            (90, "irrigation", "Pre-flowering irrigation — critical for grain filling."),
            (120, "harvest", "Wheat is approaching maturity. Check grain hardness. Arrange harvester."),
        ],
        "rice": [
            (15, "fertilizer", "First top-dressing of urea (20 kg/acre) — active tillering."),
            (30, "pest_check", "Scout for stem borer and leaf folder. Check for dead hearts."),
            (45, "fertilizer", "Second top-dressing of urea (15 kg/acre) — panicle initiation."),
            (60, "pest_check", "Check for blast disease and BPH. Critical stage."),
            (90, "irrigation", "Drain water 10 days before harvest for uniform maturity."),
            (100, "harvest", "Rice approaching harvest. Check grain moisture (20-22%)."),
        ],
        "cotton": [
            (20, "irrigation", "First irrigation if no rain. Check for germination gaps."),
            (35, "fertilizer", "Apply urea 25 kg/acre + potash. Square formation stage."),
            (50, "pest_check", "Scout for bollworm eggs on terminals. Install pheromone traps."),
            (75, "pest_check", "Peak bollworm period. Spray if 5+ larvae per 20 plants."),
            (120, "harvest", "First cotton picking ready. Pick open bolls, avoid green bolls."),
        ],
        "maize": [
            (15, "fertilizer", "Side-dress urea 25 kg/acre — knee-high stage."),
            (25, "pest_check", "Check whorl for fall armyworm. Scout early morning."),
            (45, "fertilizer", "Second urea dose 20 kg/acre — tasseling stage."),
            (70, "irrigation", "Critical irrigation at grain filling stage."),
            (90, "harvest", "Check cob maturity. Harvest when grain moisture is 25%."),
        ],
        "tomato": [
            (7, "irrigation", "Ensure regular irrigation. Mulch around plants."),
            (21, "fertilizer", "Apply NPK 19:19:19 foliar spray. Stake plants now."),
            (30, "pest_check", "Check for whitefly and leaf curl virus. Yellow sticky traps."),
            (45, "pest_check", "Scout for fruit borer. Spray neem oil preventively."),
            (60, "harvest", "First harvest approaching. Pick at breaker stage for better shelf life."),
        ],
    }

    crop_lower = crop.lower()
    templates = reminders_template.get(crop_lower, [
        (21, "irrigation", f"Check {crop} irrigation needs — 3 weeks since planting."),
        (42, "fertilizer", f"Consider top-dressing fertilizer for {crop}."),
        (60, "pest_check", f"Scout {crop} for pests and diseases."),
    ])

    for days_offset, rtype, message in templates:
        due = (base + timedelta(days=days_offset)).strftime("%Y-%m-%d")
        reminder = CropReminder(
            farmer_id=farmer_id,
            crop=crop,
            reminder_type=rtype,
            message=message,
            due_date=due,
        )
        db.add(reminder)


def get_diary_entries(db: Session, farmer_id: int) -> list[CropDiaryEntry]:
    return db.query(CropDiaryEntry).filter(
        CropDiaryEntry.farmer_id == farmer_id
    ).order_by(CropDiaryEntry.date_recorded.desc()).limit(50).all()


def get_pending_reminders(db: Session, farmer_id: int) -> list[CropReminder]:
    today = date.today().isoformat()
    return db.query(CropReminder).filter(
        CropReminder.farmer_id == farmer_id,
        CropReminder.completed == 0,
        CropReminder.due_date <= today,
    ).order_by(CropReminder.due_date).all()


def get_upcoming_reminders(db: Session, farmer_id: int, days: int = 14) -> list[CropReminder]:
    today = date.today()
    future = (today + timedelta(days=days)).isoformat()
    return db.query(CropReminder).filter(
        CropReminder.farmer_id == farmer_id,
        CropReminder.completed == 0,
        CropReminder.due_date <= future,
    ).order_by(CropReminder.due_date).all()


# --- PDF REPORT (simple text report for now, can convert to PDF with lib) ---
def generate_farmer_report(db: Session, farmer_id: int, farmer_data: dict) -> str:
    """Generate a text report for the farmer (can be rendered as PDF on frontend)."""
    from app.models.call import CallLog
    from app.models.farmer import FarmerExpense

    calls = db.query(CallLog).filter(CallLog.session_id.contains(str(farmer_id))).limit(10).all()
    expenses = db.query(FarmerExpense).filter(FarmerExpense.farmer_id == farmer_id).all()
    diary = get_diary_entries(db, farmer_id)
    reminders = get_upcoming_reminders(db, farmer_id, 30)

    total_expense = sum(e.amount for e in expenses)

    report = f"""
═══════════════════════════════════════
         KISANVAANI FARMER REPORT
═══════════════════════════════════════

Name: {farmer_data.get('name', 'N/A')}
Location: {', '.join(filter(None, [farmer_data.get('village'), farmer_data.get('district'), farmer_data.get('region')]))}
Country: {farmer_data.get('country', 'N/A')}
Land: {farmer_data.get('land_size_acres', 'N/A')} acres
Soil: {farmer_data.get('soil_type', 'N/A')}
Irrigation: {farmer_data.get('irrigation_type', 'N/A')}
Crops: {', '.join(farmer_data.get('crops', []))}

───────────────────────────────────────
EXPENSE SUMMARY
───────────────────────────────────────
Total Spent: Rs {total_expense:,.0f}
Number of Expenses: {len(expenses)}
"""
    for e in expenses:
        report += f"  - {e.category}: Rs {e.amount:,.0f} ({e.description})\n"

    report += f"""
───────────────────────────────────────
CROP DIARY ({len(diary)} entries)
───────────────────────────────────────
"""
    for d in diary[:10]:
        report += f"  {d.date_recorded} | {d.crop} | {d.activity} | {d.details}\n"

    report += f"""
───────────────────────────────────────
UPCOMING REMINDERS ({len(reminders)})
───────────────────────────────────────
"""
    for r in reminders[:10]:
        report += f"  {r.due_date} | {r.crop} | {r.reminder_type} | {r.message[:60]}\n"

    report += f"""
───────────────────────────────────────
CALL HISTORY ({len(calls)} recent)
───────────────────────────────────────
"""
    for c in calls[:5]:
        report += f"  Q: {c.farmer_question[:60]}...\n"
        report += f"  A: {c.ai_response[:60]}...\n\n"

    report += """
═══════════════════════════════════════
Generated by KisanVaani — AI Farm Advisor
https://kisanvaani.in
═══════════════════════════════════════
"""
    return report
