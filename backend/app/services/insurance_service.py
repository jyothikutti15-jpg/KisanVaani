"""Crop Insurance Auto-Claims — Generate insurance claim data from crop diary + photo evidence.

Farmers often lose insurance claims because they can't document damage properly.
This service auto-generates claim packages using:
1. Crop diary entries (planting date, activities, expenses)
2. Photo evidence (already uploaded for diagnosis)
3. Weather data (proof of adverse conditions)
4. Satellite NDVI data (proof of crop stress)
"""
import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.crop_diary import CropDiaryEntry
from app.models.farmer import FarmerExpense, FarmerProfile
from app.models.marketplace import SatelliteReport

logger = logging.getLogger("kisanvaani.insurance")

# Insurance schemes by country
INSURANCE_SCHEMES = {
    "IN": {
        "pmfby": {
            "name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
            "coverage": "Covers crop loss from natural calamities, pests, diseases",
            "premium": "Kharif: 2%, Rabi: 1.5%, Horticulture: 5%",
            "claim_within": "72 hours of crop loss",
            "documents": [
                "Aadhaar Card", "Land Records (7/12 extract)", "Sowing Certificate",
                "Bank Account Details", "Crop Damage Photos", "Weather Report"
            ],
            "contact": "Crop Insurance Portal: pmfby.gov.in | Helpline: 1800-200-7710",
            "where_to_file": "Nearest bank branch or Common Service Center (CSC)",
        },
        "rwbcis": {
            "name": "Restructured Weather Based Crop Insurance (RWBCIS)",
            "coverage": "Weather-based triggers — no field inspection needed",
            "premium": "Same as PMFBY",
            "claim_within": "Automatic trigger based on weather data",
            "documents": ["Aadhaar Card", "Land Records", "Bank Account"],
            "contact": "Agriculture Insurance Company: 1800-116-515",
            "where_to_file": "Automatic — linked to weather stations",
        },
    },
    "KE": {
        "acre": {
            "name": "Agriculture and Climate Risk Enterprise (ACRE Africa)",
            "coverage": "Index-based crop and livestock insurance",
            "premium": "5-10% of sum insured",
            "claim_within": "Automatic trigger based on satellite/weather data",
            "documents": ["National ID", "Farm Details", "Mobile Money Account"],
            "contact": "ACRE Africa: +254-20-271-8544",
            "where_to_file": "Through registered agents or mobile",
        },
    },
    "NG": {
        "naic": {
            "name": "Nigeria Agricultural Insurance Corporation (NAIC)",
            "coverage": "Crop, livestock, poultry, fishery insurance",
            "premium": "Subsidized 50% by government",
            "claim_within": "48 hours of loss event",
            "documents": ["Farm Registration", "NIN/BVN", "Crop Photos", "Loss Report"],
            "contact": "NAIC: +234-9-234-6403",
            "where_to_file": "NAIC state offices or through extension agents",
        },
    },
}


def generate_claim_package(
    db: Session,
    farmer_id: int,
    crop: str,
    damage_type: str,  # drought, flood, pest, disease, hail, other
    damage_description: str,
    country: str = "IN",
) -> dict:
    """Generate a complete insurance claim package from farmer data.

    Pulls together:
    - Farmer profile (land size, location)
    - Crop diary (planting date, activities)
    - Expenses (total investment in the crop)
    - Satellite reports (NDVI evidence)
    - Claim form guidance
    """
    farmer = db.query(FarmerProfile).filter(FarmerProfile.id == farmer_id).first()
    if not farmer:
        return {"error": "Farmer not found"}

    # Get crop diary entries
    diary_entries = (
        db.query(CropDiaryEntry)
        .filter(CropDiaryEntry.farmer_id == farmer_id, CropDiaryEntry.crop.contains(crop))
        .order_by(CropDiaryEntry.date_recorded.asc())
        .all()
    )

    # Get expenses for this crop
    expenses = (
        db.query(FarmerExpense)
        .filter(FarmerExpense.farmer_id == farmer_id)
        .filter((FarmerExpense.crop.contains(crop)) | (FarmerExpense.crop.is_(None)))
        .all()
    )
    total_investment = sum(e.amount for e in expenses if e.amount)

    # Get satellite reports
    satellite_reports = (
        db.query(SatelliteReport)
        .filter(SatelliteReport.farmer_id == farmer_id)
        .order_by(SatelliteReport.created_at.desc())
        .limit(5)
        .all()
    )

    # Find planting date
    planting_date = None
    for entry in diary_entries:
        if entry.activity == "planted":
            planting_date = entry.date_recorded
            break

    # Calculate days since planting
    days_since_planting = None
    if planting_date:
        try:
            plant_dt = datetime.strptime(planting_date, "%Y-%m-%d")
            days_since_planting = (datetime.now() - plant_dt).days
        except ValueError:
            pass

    # Get applicable insurance schemes
    country_schemes = INSURANCE_SCHEMES.get(country, INSURANCE_SCHEMES.get("IN", {}))

    # Build claim package
    claim = {
        "claim_id": f"KV-{farmer_id}-{datetime.now().strftime('%Y%m%d')}",
        "generated_at": datetime.now().isoformat(),
        "status": "draft",

        "farmer_details": {
            "name": farmer.name,
            "farmer_id": farmer.id,
            "region": farmer.region,
            "district": farmer.district,
            "village": farmer.village,
            "country": farmer.country or country,
            "land_size_acres": farmer.land_size_acres,
        },

        "crop_details": {
            "crop": crop,
            "planting_date": planting_date,
            "days_since_planting": days_since_planting,
            "crop_stage": _get_crop_stage(days_since_planting),
            "total_activities_logged": len(diary_entries),
        },

        "damage_details": {
            "damage_type": damage_type,
            "description": damage_description,
            "reported_date": datetime.now().strftime("%Y-%m-%d"),
        },

        "financial_evidence": {
            "total_investment": total_investment,
            "expense_count": len(expenses),
            "expenses_breakdown": [
                {"category": e.category, "amount": e.amount, "description": e.description}
                for e in expenses[:10]
            ],
        },

        "crop_diary_evidence": [
            {"date": e.date_recorded, "activity": e.activity, "details": e.details}
            for e in diary_entries
        ],

        "satellite_evidence": [
            {
                "date": r.satellite_date,
                "ndvi_score": r.ndvi_score,
                "health_status": r.health_status,
                "analysis": r.analysis[:200] if r.analysis else None,
            }
            for r in satellite_reports
        ],

        "applicable_schemes": [
            {
                "scheme_id": sid,
                "name": scheme["name"],
                "coverage": scheme["coverage"],
                "premium": scheme["premium"],
                "claim_deadline": scheme["claim_within"],
                "required_documents": scheme["documents"],
                "contact": scheme["contact"],
                "where_to_file": scheme["where_to_file"],
            }
            for sid, scheme in country_schemes.items()
        ],

        "next_steps": _generate_next_steps(damage_type, country, planting_date),
    }

    logger.info(f"Insurance claim package generated: {claim['claim_id']} for farmer {farmer_id}, crop={crop}")
    return claim


def _get_crop_stage(days: Optional[int]) -> str:
    if days is None:
        return "unknown"
    if days < 15:
        return "seedling"
    elif days < 35:
        return "vegetative"
    elif days < 60:
        return "flowering"
    elif days < 90:
        return "fruiting"
    elif days < 120:
        return "maturity"
    else:
        return "harvest-ready"


def _generate_next_steps(damage_type: str, country: str, planting_date: Optional[str]) -> list[str]:
    steps = [
        "Take clear photos of crop damage from multiple angles",
        "Take photos of the full field showing extent of damage",
        "Note the date and time of the damage event",
    ]

    if damage_type in ("drought", "flood", "hail"):
        steps.append("Get weather report from nearest meteorological station")
        steps.append("Collect newspaper clippings mentioning the weather event")

    if damage_type in ("pest", "disease"):
        steps.append("Collect samples of affected plants in a sealed bag")
        steps.append("Contact local KVK/extension officer for field inspection")

    if country == "IN":
        steps.extend([
            "File claim at nearest bank branch or CSC within 72 hours",
            "Call PMFBY helpline: 1800-200-7710",
            "Keep all original purchase receipts for seeds, fertilizer, pesticide",
            "Get Sarpanch/Patwari to sign a crop damage certificate",
        ])
    elif country == "KE":
        steps.extend([
            "Contact ACRE Africa agent or call +254-20-271-8544",
            "Index-based claims may trigger automatically from satellite data",
        ])
    elif country == "NG":
        steps.extend([
            "Report to NAIC state office within 48 hours",
            "Contact your ADP extension agent for field inspection",
        ])

    return steps


def get_insurance_schemes(country: str) -> list[dict]:
    """Get all insurance schemes for a country."""
    schemes = INSURANCE_SCHEMES.get(country, {})
    return [
        {"id": sid, "name": s["name"], "coverage": s["coverage"],
         "premium": s["premium"], "contact": s["contact"]}
        for sid, s in schemes.items()
    ]
