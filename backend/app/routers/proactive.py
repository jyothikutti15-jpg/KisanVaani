"""Proactive outbound calls — scheduling, delivery, and management."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.proactive import ScheduledCall
from app.services.proactive_service import (
    deliver_call, get_pending_calls, schedule_proactive_calls,
)

logger = logging.getLogger("kisanvaani.proactive")
router = APIRouter(prefix="/api/proactive", tags=["proactive"])


@router.post("/generate")
def generate_scheduled_calls(db: Session = Depends(get_db)):
    """Generate proactive calls for all farmers based on their crop diary, weather, and alerts.
    Call this endpoint daily (via cron/scheduler) to keep reminders fresh.
    """
    stats = schedule_proactive_calls(db)
    return {"status": "ok", "scheduled": stats}


@router.post("/deliver")
def deliver_pending_calls(limit: int = 20, db: Session = Depends(get_db)):
    """Deliver pending scheduled calls via WhatsApp/voice.
    Call this endpoint every 15-30 minutes to process the queue.
    """
    pending = get_pending_calls(db, limit)
    results = {"delivered": 0, "failed": 0, "total": len(pending)}

    for call in pending:
        status = deliver_call(db, call)
        if status in ("sent", "mock_sent"):
            results["delivered"] += 1
        else:
            results["failed"] += 1

    return results


@router.get("/queue")
def get_call_queue(
    status: Optional[str] = None,
    farmer_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """View the scheduled call queue."""
    query = db.query(ScheduledCall)
    if status:
        query = query.filter(ScheduledCall.status == status)
    if farmer_id:
        query = query.filter(ScheduledCall.farmer_id == farmer_id)

    calls = query.order_by(ScheduledCall.scheduled_for.desc()).limit(limit).all()
    return [
        {
            "id": c.id,
            "farmer_id": c.farmer_id,
            "type": c.call_type,
            "title": c.title,
            "message": c.message[:200],
            "language": c.language,
            "status": c.status,
            "priority": c.priority,
            "scheduled_for": str(c.scheduled_for),
            "sent_at": str(c.sent_at) if c.sent_at else None,
            "attempts": c.attempts,
        }
        for c in calls
    ]


@router.get("/stats")
def proactive_stats(db: Session = Depends(get_db)):
    """Get proactive call statistics."""
    total = db.query(ScheduledCall).count()
    pending = db.query(ScheduledCall).filter(ScheduledCall.status == "pending").count()
    sent = db.query(ScheduledCall).filter(ScheduledCall.status == "sent").count()
    failed = db.query(ScheduledCall).filter(ScheduledCall.status == "failed").count()

    # Type breakdown
    from sqlalchemy import func
    type_counts = (
        db.query(ScheduledCall.call_type, func.count(ScheduledCall.id))
        .group_by(ScheduledCall.call_type)
        .all()
    )

    return {
        "total": total,
        "pending": pending,
        "sent": sent,
        "failed": failed,
        "by_type": {t: c for t, c in type_counts},
    }
