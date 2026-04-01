import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.farmer import FarmerProfile

router = APIRouter(prefix="/api/farmers", tags=["farmers"])


class FarmerCreate(BaseModel):
    name: Optional[str] = None
    preferred_language: str = "hi"
    country: str = "IN"
    region: Optional[str] = None
    district: Optional[str] = None
    village: Optional[str] = None
    land_size_acres: Optional[float] = None
    crops: list[str] = []
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None
    phone_hash: Optional[str] = None


class FarmerResponse(BaseModel):
    id: int
    name: Optional[str] = None
    preferred_language: str
    country: str
    region: Optional[str] = None
    district: Optional[str] = None
    village: Optional[str] = None
    land_size_acres: Optional[float] = None
    crops: list[str] = []
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None
    past_problems: list[str] = []
    active_issues: list[str] = []
    total_calls: int = 0

    model_config = {"from_attributes": True}


def _farmer_to_response(f: FarmerProfile) -> FarmerResponse:
    return FarmerResponse(
        id=f.id,
        name=f.name,
        preferred_language=f.preferred_language,
        country=f.country,
        region=f.region,
        district=f.district,
        village=f.village,
        land_size_acres=f.land_size_acres,
        crops=json.loads(f.crops) if f.crops else [],
        soil_type=f.soil_type,
        irrigation_type=f.irrigation_type,
        past_problems=json.loads(f.past_problems) if f.past_problems else [],
        active_issues=json.loads(f.active_issues) if f.active_issues else [],
        total_calls=f.total_calls,
    )


@router.post("", response_model=FarmerResponse, status_code=201)
def create_farmer(data: FarmerCreate, db: Session = Depends(get_db)):
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
        phone_hash=data.phone_hash,
    )
    db.add(farmer)
    db.commit()
    db.refresh(farmer)
    return _farmer_to_response(farmer)


@router.get("", response_model=list[FarmerResponse])
def list_farmers(country: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(FarmerProfile).order_by(FarmerProfile.last_call.desc())
    if country:
        query = query.filter(FarmerProfile.country == country)
    return [_farmer_to_response(f) for f in query.limit(100).all()]


@router.get("/{farmer_id}", response_model=FarmerResponse)
def get_farmer(farmer_id: int, db: Session = Depends(get_db)):
    farmer = db.query(FarmerProfile).filter(FarmerProfile.id == farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return _farmer_to_response(farmer)


@router.put("/{farmer_id}", response_model=FarmerResponse)
def update_farmer(farmer_id: int, data: FarmerCreate, db: Session = Depends(get_db)):
    farmer = db.query(FarmerProfile).filter(FarmerProfile.id == farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")

    for field in ["name", "preferred_language", "country", "region", "district",
                  "village", "land_size_acres", "soil_type", "irrigation_type"]:
        val = getattr(data, field, None)
        if val is not None:
            setattr(farmer, field, val)
    if data.crops:
        farmer.crops = json.dumps(data.crops)

    db.commit()
    db.refresh(farmer)
    return _farmer_to_response(farmer)
