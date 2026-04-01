from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import SUPPORTED_LANGUAGES
from app.database import get_db
from app.models.call import CallLog
from app.schemas.voice import AnalyticsOverview, CallLogResponse, DailyCallStat, LanguageStat

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/analytics/overview", response_model=AnalyticsOverview)
def get_overview(db: Session = Depends(get_db)):
    total = db.query(func.count(CallLog.id)).scalar() or 0
    unique = db.query(func.count(func.distinct(CallLog.session_id))).scalar() or 0
    langs = db.query(func.count(func.distinct(CallLog.language))).scalar() or 0
    today_str = date.today().isoformat()
    today_count = db.query(func.count(CallLog.id)).filter(
        func.date(CallLog.created_at) == today_str
    ).scalar() or 0

    return AnalyticsOverview(
        total_calls=total,
        unique_sessions=unique,
        languages_served=langs,
        calls_today=today_count,
    )


@router.get("/analytics/languages", response_model=list[LanguageStat])
def get_language_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(CallLog.id)).scalar() or 1
    rows = db.query(CallLog.language, func.count(CallLog.id)).group_by(CallLog.language).all()

    stats = []
    for lang, count in rows:
        lang_info = SUPPORTED_LANGUAGES.get(lang, {})
        stats.append(LanguageStat(
            language=lang,
            language_name=lang_info.get("name", lang),
            count=count,
            percentage=round(count / total * 100, 1),
        ))
    return sorted(stats, key=lambda s: s.count, reverse=True)


@router.get("/analytics/timeline", response_model=list[DailyCallStat])
def get_call_timeline(days: int = 30, db: Session = Depends(get_db)):
    start_date = date.today() - timedelta(days=days)
    rows = (
        db.query(func.date(CallLog.created_at), func.count(CallLog.id))
        .filter(func.date(CallLog.created_at) >= start_date.isoformat())
        .group_by(func.date(CallLog.created_at))
        .all()
    )

    date_counts = {str(d): c for d, c in rows}
    result = []
    for i in range(days + 1):
        d = (start_date + timedelta(days=i)).isoformat()
        result.append(DailyCallStat(date=d, count=date_counts.get(d, 0)))
    return result


@router.get("/calls", response_model=list[CallLogResponse])
def get_call_history(
    skip: int = 0,
    limit: int = 50,
    language: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(CallLog).order_by(CallLog.created_at.desc())
    if language:
        query = query.filter(CallLog.language == language)
    calls = query.offset(skip).limit(limit).all()

    return [
        CallLogResponse(
            id=c.id,
            session_id=c.session_id,
            source=c.source,
            phone_number=c.phone_number,
            language=c.language,
            farmer_question=c.farmer_question,
            ai_response=c.ai_response,
            category=c.category,
            created_at=str(c.created_at),
        )
        for c in calls
    ]
