import json
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.alert import Alert, CommunityInsight

router = APIRouter(prefix="/api", tags=["alerts"])


class AlertCreate(BaseModel):
    alert_type: str
    severity: str
    title: str
    message: str
    country: str = "IN"
    region: Optional[str] = None
    affected_crops: list[str] = []
    source: Optional[str] = None


class AlertResponse(BaseModel):
    id: int
    alert_type: str
    severity: str
    title: str
    message: str
    country: str
    region: Optional[str] = None
    affected_crops: list[str] = []
    source: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}


class CommunityInsightResponse(BaseModel):
    id: int
    region: str
    country: str
    topic: str
    affected_crop: Optional[str] = None
    farmer_count: int
    trending: bool
    ai_summary: Optional[str] = None
    last_reported: str

    model_config = {"from_attributes": True}


@router.post("/alerts", response_model=AlertResponse, status_code=201)
def create_alert(data: AlertCreate, db: Session = Depends(get_db)):
    alert = Alert(
        alert_type=data.alert_type,
        severity=data.severity,
        title=data.title,
        message=data.message,
        country=data.country,
        region=data.region,
        affected_crops=json.dumps(data.affected_crops),
        source=data.source,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return _alert_response(alert)


@router.get("/alerts", response_model=list[AlertResponse])
def list_alerts(country: Optional[str] = None, active_only: bool = True, db: Session = Depends(get_db)):
    query = db.query(Alert).order_by(desc(Alert.created_at))
    if country:
        query = query.filter(Alert.country == country)
    if active_only:
        query = query.filter(Alert.active == 1)
    alerts = query.limit(50).all()
    return [_alert_response(a) for a in alerts]


@router.get("/community", response_model=list[CommunityInsightResponse])
def get_community_insights(country: Optional[str] = None, region: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(CommunityInsight).order_by(desc(CommunityInsight.farmer_count))
    if country:
        query = query.filter(CommunityInsight.country == country)
    if region:
        query = query.filter(CommunityInsight.region == region)
    insights = query.limit(20).all()
    return [
        CommunityInsightResponse(
            id=i.id, region=i.region, country=i.country, topic=i.topic,
            affected_crop=i.affected_crop, farmer_count=i.farmer_count,
            trending=bool(i.trending), ai_summary=i.ai_summary,
            last_reported=str(i.last_reported),
        )
        for i in insights
    ]


def _alert_response(a: Alert) -> AlertResponse:
    return AlertResponse(
        id=a.id, alert_type=a.alert_type, severity=a.severity,
        title=a.title, message=a.message, country=a.country,
        region=a.region,
        affected_crops=json.loads(a.affected_crops) if a.affected_crops else [],
        source=a.source, created_at=str(a.created_at),
    )
