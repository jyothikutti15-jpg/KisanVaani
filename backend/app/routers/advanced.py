"""Advanced feature routes: Expert Callbacks, Marketplace, Satellite Monitoring, Price Prediction, Farmer Network."""
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.marketplace import ExpertCallback, FarmerQuestion, MarketListing, SatelliteReport
from app.services.price_predictor import get_price_trends, predict_price
from app.services.satellite_service import (
    analyze_by_location_name, analyze_field_health,
    get_farmer_satellite_history,
)

logger = logging.getLogger("kisanvaani.advanced")
router = APIRouter(prefix="/api", tags=["advanced"])


# ────────────────────────────────
# PRICE PREDICTION
# ────────────────────────────────

@router.get("/prices/predict/{crop}")
async def predict_crop_price(
    crop: str,
    days: int = 7,
    country: str = "IN",
    db: Session = Depends(get_db),
):
    """Predict future mandi price for a crop.

    Returns current price, predicted price, confidence range,
    and buy/sell/hold recommendation.
    """
    result = predict_price(db, crop, days_ahead=days, country=country)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/prices/trends/{crop}")
async def crop_price_trends(
    crop: str,
    days: int = 30,
    db: Session = Depends(get_db),
):
    """Get historical price trend data for a crop (for charts)."""
    trends = get_price_trends(db, crop, days)
    if not trends:
        raise HTTPException(status_code=404, detail=f"No price history for '{crop}'")
    return {"crop": crop, "days": days, "prices": trends}


# ────────────────────────────────
# SATELLITE CROP HEALTH
# ────────────────────────────────

class SatelliteAnalysisRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location: Optional[str] = None  # Alternative: use location name
    crop: Optional[str] = None
    farmer_id: Optional[int] = None
    country: str = "IN"


@router.post("/satellite/analyze")
async def satellite_analysis(body: SatelliteAnalysisRequest, db: Session = Depends(get_db)):
    """Analyze crop health from satellite data (NDVI).

    Provide either lat/lon coordinates or a location name.
    Returns health score, status, analysis, and recommendations.
    """
    if body.location:
        result = await analyze_by_location_name(
            db, body.location, body.crop, body.farmer_id, body.country,
        )
    elif body.latitude is not None and body.longitude is not None:
        result = await analyze_field_health(
            db, body.latitude, body.longitude, body.crop, body.farmer_id,
            country=body.country,
        )
    else:
        raise HTTPException(status_code=400, detail="Provide location name or lat/lon coordinates")

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/satellite/history/{farmer_id}")
async def satellite_history(farmer_id: int, limit: int = 10, db: Session = Depends(get_db)):
    """Get satellite monitoring history for a farmer."""
    return get_farmer_satellite_history(db, farmer_id, limit)


@router.get("/satellite/regional/{location}")
async def regional_satellite(
    location: str,
    crop: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get regional crop health overview from satellite data."""
    result = await analyze_by_location_name(db, location, crop)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ────────────────────────────────
# EXPERT CALLBACK SYSTEM
# ────────────────────────────────

class ExpertCallbackRequest(BaseModel):
    farmer_id: int
    question: str
    ai_response: Optional[str] = None
    ai_confidence: str = "low"  # low, uncertain
    reason: Optional[str] = None
    category: Optional[str] = None  # pest, disease, soil, livestock, legal
    phone_number: Optional[str] = None
    language: str = "hi"
    country: str = "IN"
    region: Optional[str] = None


@router.post("/expert/request")
async def request_expert_callback(body: ExpertCallbackRequest, db: Session = Depends(get_db)):
    """Request a human expert callback when AI can't confidently answer.

    Creates a ticket in the expert queue. Experts can view pending tickets
    and provide responses that are delivered back to the farmer.
    """
    # Get farmer name
    from app.models.farmer import FarmerProfile
    farmer = db.query(FarmerProfile).filter(FarmerProfile.id == body.farmer_id).first()

    callback = ExpertCallback(
        farmer_id=body.farmer_id,
        farmer_name=farmer.name if farmer else None,
        phone_number=body.phone_number,
        language=body.language,
        question=body.question,
        ai_response=body.ai_response,
        ai_confidence=body.ai_confidence,
        reason=body.reason or "AI confidence below threshold",
        category=body.category,
        region=body.region or (farmer.region if farmer else None),
        country=body.country,
        priority=1 if body.category in ("disease", "livestock") else 2,
    )
    db.add(callback)
    db.commit()
    db.refresh(callback)

    logger.info(f"Expert callback requested: #{callback.id} for farmer {body.farmer_id}, category={body.category}")

    return {
        "ticket_id": callback.id,
        "status": "pending",
        "message": "Your question has been sent to a farming expert. You will receive a callback within 48 hours.",
        "priority": callback.priority,
    }


@router.get("/expert/queue")
async def expert_queue(
    status: str = "pending",
    category: Optional[str] = None,
    country: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """View the expert callback queue (for expert dashboard)."""
    query = db.query(ExpertCallback).filter(ExpertCallback.status == status)
    if category:
        query = query.filter(ExpertCallback.category == category)
    if country:
        query = query.filter(ExpertCallback.country == country)

    tickets = query.order_by(ExpertCallback.priority.asc(), ExpertCallback.created_at.asc()).limit(limit).all()

    return [
        {
            "id": t.id,
            "farmer_id": t.farmer_id,
            "farmer_name": t.farmer_name,
            "question": t.question,
            "ai_response": t.ai_response,
            "ai_confidence": t.ai_confidence,
            "category": t.category,
            "region": t.region,
            "country": t.country,
            "language": t.language,
            "priority": t.priority,
            "status": t.status,
            "created_at": str(t.created_at),
        }
        for t in tickets
    ]


class ExpertResponseRequest(BaseModel):
    expert_name: str
    response: str


@router.post("/expert/{ticket_id}/resolve")
async def resolve_expert_ticket(
    ticket_id: int,
    body: ExpertResponseRequest,
    db: Session = Depends(get_db),
):
    """Expert resolves a callback ticket with their response."""
    ticket = db.query(ExpertCallback).filter(ExpertCallback.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = "resolved"
    ticket.assigned_expert = body.expert_name
    ticket.expert_response = body.response
    ticket.resolved_at = datetime.now()
    db.commit()

    logger.info(f"Expert ticket #{ticket_id} resolved by {body.expert_name}")

    return {
        "ticket_id": ticket_id,
        "status": "resolved",
        "message": "Response saved. Farmer will be notified.",
    }


@router.get("/expert/stats")
async def expert_stats(db: Session = Depends(get_db)):
    """Expert callback system statistics."""
    total = db.query(ExpertCallback).count()
    pending = db.query(ExpertCallback).filter(ExpertCallback.status == "pending").count()
    resolved = db.query(ExpertCallback).filter(ExpertCallback.status == "resolved").count()

    # Average resolution time
    resolved_tickets = (
        db.query(ExpertCallback)
        .filter(ExpertCallback.status == "resolved", ExpertCallback.resolved_at.isnot(None))
        .all()
    )
    avg_hours = 0
    if resolved_tickets:
        total_hours = sum(
            (t.resolved_at - t.created_at).total_seconds() / 3600
            for t in resolved_tickets
            if t.resolved_at and t.created_at
        )
        avg_hours = round(total_hours / len(resolved_tickets), 1)

    # By category
    category_counts = (
        db.query(ExpertCallback.category, func.count(ExpertCallback.id))
        .filter(ExpertCallback.status == "pending")
        .group_by(ExpertCallback.category)
        .all()
    )

    return {
        "total": total,
        "pending": pending,
        "resolved": resolved,
        "avg_resolution_hours": avg_hours,
        "pending_by_category": {c or "uncategorized": n for c, n in category_counts},
    }


# ────────────────────────────────
# FARMER-TO-FARMER NETWORK
# ────────────────────────────────

class ShareQuestionRequest(BaseModel):
    region: str
    country: str = "IN"
    crop: Optional[str] = None
    question_summary: str
    ai_answer: str
    category: Optional[str] = None
    language: str = "en"


@router.post("/community/share")
async def share_farmer_question(body: ShareQuestionRequest, db: Session = Depends(get_db)):
    """Share an anonymized farmer Q&A to the community network.

    Other farmers in the same region can see what problems nearby farmers face
    and what solutions worked — creating peer-to-peer learning.
    """
    question = FarmerQuestion(
        region=body.region,
        country=body.country,
        crop=body.crop,
        question_summary=body.question_summary,
        ai_answer=body.ai_answer,
        category=body.category,
        language=body.language,
    )
    db.add(question)
    db.commit()
    return {"id": question.id, "status": "shared"}


@router.get("/community/questions")
async def get_community_questions(
    region: Optional[str] = None,
    country: Optional[str] = None,
    crop: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Browse anonymized Q&A from nearby farmers.

    'What are farmers near me asking about?'
    """
    query = db.query(FarmerQuestion)
    if region:
        query = query.filter(FarmerQuestion.region.contains(region))
    if country:
        query = query.filter(FarmerQuestion.country == country)
    if crop:
        query = query.filter(FarmerQuestion.crop.contains(crop))
    if category:
        query = query.filter(FarmerQuestion.category == category)

    questions = query.order_by(FarmerQuestion.helpful_count.desc(), FarmerQuestion.created_at.desc()).limit(limit).all()

    return [
        {
            "id": q.id,
            "region": q.region,
            "crop": q.crop,
            "question": q.question_summary,
            "answer": q.ai_answer,
            "category": q.category,
            "helpful_count": q.helpful_count,
            "language": q.language,
            "created_at": str(q.created_at),
        }
        for q in questions
    ]


@router.post("/community/questions/{question_id}/helpful")
async def mark_helpful(question_id: int, db: Session = Depends(get_db)):
    """Mark a community Q&A as helpful (upvote)."""
    q = db.query(FarmerQuestion).filter(FarmerQuestion.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    q.helpful_count = (q.helpful_count or 0) + 1
    db.commit()
    return {"id": question_id, "helpful_count": q.helpful_count}


@router.get("/community/trending")
async def trending_topics(
    country: Optional[str] = None,
    days: int = 7,
    db: Session = Depends(get_db),
):
    """Get trending farming topics from the community.

    Shows what problems are being reported most frequently.
    """
    since = datetime.now() - timedelta(days=days)
    query = (
        db.query(
            FarmerQuestion.category,
            FarmerQuestion.crop,
            FarmerQuestion.region,
            func.count(FarmerQuestion.id).label("count"),
        )
        .filter(FarmerQuestion.created_at >= since)
    )
    if country:
        query = query.filter(FarmerQuestion.country == country)

    trends = (
        query.group_by(FarmerQuestion.category, FarmerQuestion.crop, FarmerQuestion.region)
        .order_by(func.count(FarmerQuestion.id).desc())
        .limit(10)
        .all()
    )

    return [
        {
            "category": t.category,
            "crop": t.crop,
            "region": t.region,
            "report_count": t.count,
        }
        for t in trends
    ]


# ────────────────────────────────
# MARKETPLACE (BUY/SELL)
# ────────────────────────────────

class ListingCreate(BaseModel):
    farmer_id: int
    listing_type: str  # sell, buy
    crop: str
    quantity: str  # "5 quintals"
    price_per_unit: Optional[float] = None
    unit: str = "quintal"
    region: str
    district: Optional[str] = None
    country: str = "IN"
    phone_number: Optional[str] = None
    description: Optional[str] = None


@router.post("/marketplace/listings")
async def create_listing(body: ListingCreate, db: Session = Depends(get_db)):
    """Create a buy/sell listing on the farmer marketplace.

    Connects farmers directly with buyers — no middleman.
    """
    from app.models.farmer import FarmerProfile
    farmer = db.query(FarmerProfile).filter(FarmerProfile.id == body.farmer_id).first()

    listing = MarketListing(
        farmer_id=body.farmer_id,
        farmer_name=farmer.name if farmer else None,
        listing_type=body.listing_type,
        crop=body.crop,
        quantity=body.quantity,
        price_per_unit=body.price_per_unit,
        unit=body.unit,
        region=body.region,
        district=body.district,
        country=body.country,
        phone_number=body.phone_number,
        description=body.description,
        expires_at=datetime.now() + timedelta(days=30),
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)

    logger.info(f"Marketplace listing #{listing.id}: {body.listing_type} {body.crop} in {body.region}")

    return {
        "id": listing.id,
        "status": "active",
        "message": f"Your {body.listing_type} listing for {body.crop} is now live!",
        "expires": str(listing.expires_at),
    }


@router.get("/marketplace/listings")
async def browse_listings(
    crop: Optional[str] = None,
    region: Optional[str] = None,
    country: Optional[str] = None,
    listing_type: Optional[str] = None,
    limit: int = 30,
    db: Session = Depends(get_db),
):
    """Browse marketplace listings — find buyers or sellers near you."""
    query = db.query(MarketListing).filter(MarketListing.status == "active")
    if crop:
        query = query.filter(MarketListing.crop.contains(crop))
    if region:
        query = query.filter(MarketListing.region.contains(region))
    if country:
        query = query.filter(MarketListing.country == country)
    if listing_type:
        query = query.filter(MarketListing.listing_type == listing_type)

    listings = query.order_by(MarketListing.created_at.desc()).limit(limit).all()

    return [
        {
            "id": l.id,
            "farmer_name": l.farmer_name,
            "type": l.listing_type,
            "crop": l.crop,
            "quantity": l.quantity,
            "price_per_unit": l.price_per_unit,
            "unit": l.unit,
            "region": l.region,
            "district": l.district,
            "country": l.country,
            "phone": l.phone_number,
            "description": l.description,
            "created_at": str(l.created_at),
        }
        for l in listings
    ]


@router.get("/marketplace/stats")
async def marketplace_stats(country: Optional[str] = None, db: Session = Depends(get_db)):
    """Marketplace activity statistics."""
    query = db.query(MarketListing).filter(MarketListing.status == "active")
    if country:
        query = query.filter(MarketListing.country == country)

    total = query.count()
    sell = query.filter(MarketListing.listing_type == "sell").count()
    buy = query.filter(MarketListing.listing_type == "buy").count()

    # Top crops
    top_crops = (
        query.with_entities(MarketListing.crop, func.count(MarketListing.id))
        .group_by(MarketListing.crop)
        .order_by(func.count(MarketListing.id).desc())
        .limit(5)
        .all()
    )

    return {
        "total_listings": total,
        "sell_listings": sell,
        "buy_listings": buy,
        "top_crops": {c: n for c, n in top_crops},
    }
