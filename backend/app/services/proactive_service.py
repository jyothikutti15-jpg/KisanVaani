"""Proactive outbound call scheduling — sends personalized reminders to farmers.

Generates smart reminders based on:
- Crop diary (irrigation, fertilizer, pest check schedules)
- Weather alerts (rain, drought, frost warnings)
- Price spikes (sell/hold recommendations)
- Government scheme deadlines
- Weekly farming tips based on season/crop/region
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.alert import Alert
from app.models.crop_diary import CropDiaryEntry, CropReminder
from app.models.farmer import FarmerProfile
from app.models.proactive import ScheduledCall

logger = logging.getLogger("kisanvaani.proactive")

# Smart message templates by type and language
TEMPLATES = {
    "crop_reminder": {
        "hi": "Namaste {name} ji! Aapke {crop} ko {action} ka samay aa gaya hai. {detail}. Koi sawaal ho toh KisanVaani ko call karein.",
        "te": "Namaskaram {name} garu! Mee {crop} ki {action} samayam vacchindi. {detail}. Emi sandeham unte KisanVaani ki call cheyandi.",
        "en": "Hello {name}! Time for {action} on your {crop}. {detail}. Call KisanVaani if you have questions.",
        "sw": "Habari {name}! Wakati wa {action} kwa {crop} yako umefika. {detail}. Piga simu KisanVaani kwa maswali.",
        "ta": "Vanakkam {name}! Ungal {crop} kku {action} neram vandhuviddithu. {detail}. Kelvi irundhal KisanVaani kku call seyyungal.",
    },
    "weather_alert": {
        "hi": "KisanVaani Weather Alert: {title}. {message}. Apni fasal ki suraksha karein.",
        "te": "KisanVaani Vataavaranam Alert: {title}. {message}. Mee pantanu rakshninchukondandi.",
        "en": "KisanVaani Weather Alert: {title}. {message}. Protect your crops.",
        "sw": "KisanVaani Tahadhari ya Hali ya Hewa: {title}. {message}. Linda mazao yako.",
        "ta": "KisanVaani Vanilai Echcharikkai: {title}. {message}. Ungal payirai paathukkavum.",
    },
    "price_alert": {
        "hi": "{crop} ka mandi bhav {change}! Abhi {price} Rs/quintal hai. {advice}.",
        "te": "{crop} mandi dhara {change}! Ippudu {price} Rs/quintal. {advice}.",
        "en": "{crop} market price {change}! Current: Rs {price}/quintal. {advice}.",
        "sw": "Bei ya {crop} {change}! Sasa ni {price}/quintal. {advice}.",
        "ta": "{crop} sandhai vilai {change}! Ippo {price} Rs/quintal. {advice}.",
    },
    "weekly_tip": {
        "hi": "KisanVaani Weekly Tip: {tip}. Zyada jaankari ke liye call karein.",
        "en": "KisanVaani Weekly Tip: {tip}. Call us for more info.",
        "sw": "KisanVaani Kidokezo cha Wiki: {tip}. Piga simu kwa habari zaidi.",
        "te": "KisanVaani Vaara Tip: {tip}. Adhika samacharam kosam call cheyandi.",
        "ta": "KisanVaani Vaara Kurippu: {tip}. Methalanaa thakavalkku call seyyungal.",
    },
}


def generate_crop_reminders(db: Session, farmer: FarmerProfile) -> list[dict]:
    """Generate smart reminders based on farmer's crop diary."""
    reminders = []
    today = datetime.now().date()
    name = farmer.name or "Kisan"
    lang = farmer.preferred_language or "hi"

    # Get recent diary entries
    recent_entries = (
        db.query(CropDiaryEntry)
        .filter(CropDiaryEntry.farmer_id == farmer.id)
        .order_by(CropDiaryEntry.created_at.desc())
        .limit(20)
        .all()
    )

    for entry in recent_entries:
        if entry.activity == "planted" and entry.date_recorded:
            try:
                plant_date = datetime.strptime(entry.date_recorded, "%Y-%m-%d").date()
                days_since = (today - plant_date).days
            except ValueError:
                continue

            crop = entry.crop

            # Irrigation reminder (every 7-10 days)
            if days_since > 0 and days_since % 8 == 0:
                reminders.append({
                    "type": "crop_reminder",
                    "crop": crop,
                    "action": "irrigation" if lang == "en" else "sichai",
                    "detail": f"Day {days_since} since planting. Check soil moisture before watering.",
                    "schedule": today + timedelta(days=1),
                })

            # First fertilizer (21-25 days after planting)
            if 20 <= days_since <= 25:
                reminders.append({
                    "type": "crop_reminder",
                    "crop": crop,
                    "action": "first fertilizer dose" if lang == "en" else "pehla khad",
                    "detail": f"Day {days_since}: Apply urea 50kg/acre. Mix with irrigation water.",
                    "schedule": today + timedelta(days=1),
                })

            # Pest check (30 days after planting)
            if 28 <= days_since <= 32:
                reminders.append({
                    "type": "crop_reminder",
                    "crop": crop,
                    "action": "pest check" if lang == "en" else "keede ki jaanch",
                    "detail": f"Day {days_since}: Check leaf undersides for insects. Spray neem oil if found.",
                    "schedule": today,
                })

            # Second fertilizer (45-50 days)
            if 44 <= days_since <= 50:
                reminders.append({
                    "type": "crop_reminder",
                    "crop": crop,
                    "action": "second fertilizer" if lang == "en" else "doosra khad",
                    "detail": f"Day {days_since}: Apply DAP + potash. Critical for flowering stage.",
                    "schedule": today + timedelta(days=1),
                })

            # Harvest approaching (based on crop type estimates)
            harvest_days = {"wheat": 120, "rice": 130, "tomato": 75, "cotton": 160, "maize": 100}
            crop_lower = crop.lower()
            if crop_lower in harvest_days:
                days_to_harvest = harvest_days[crop_lower] - days_since
                if 5 <= days_to_harvest <= 10:
                    reminders.append({
                        "type": "crop_reminder",
                        "crop": crop,
                        "action": "harvest preparation" if lang == "en" else "katai ki taiyari",
                        "detail": f"Harvest expected in {days_to_harvest} days. Arrange labor and storage.",
                        "schedule": today + timedelta(days=2),
                    })

    return reminders


def generate_weather_alerts_for_farmer(db: Session, farmer: FarmerProfile) -> list[dict]:
    """Check active alerts relevant to this farmer."""
    alerts = []
    if not farmer.region and not farmer.country:
        return alerts

    active_alerts = (
        db.query(Alert)
        .filter(Alert.active == 1)
        .filter((Alert.country == farmer.country) | (Alert.country.is_(None)))
        .all()
    )

    for alert in active_alerts:
        # Check region match
        if alert.region and farmer.region:
            if alert.region.lower() not in farmer.region.lower() and farmer.region.lower() not in alert.region.lower():
                continue

        # Check crop overlap
        farmer_crops = []
        if farmer.crops:
            try:
                farmer_crops = [c.lower() for c in json.loads(farmer.crops)]
            except (json.JSONDecodeError, TypeError):
                farmer_crops = [farmer.crops.lower()]

        if alert.affected_crops:
            try:
                alert_crops = [c.lower() for c in json.loads(alert.affected_crops)]
                if farmer_crops and not any(c in alert_crops for c in farmer_crops):
                    continue
            except (json.JSONDecodeError, TypeError):
                pass

        alerts.append({
            "type": "weather_alert",
            "title": alert.title,
            "message": alert.message,
            "severity": alert.severity,
            "schedule": datetime.now(),
        })

    return alerts


def schedule_proactive_calls(db: Session) -> dict:
    """Generate and schedule proactive calls for all active farmers.

    This should be called periodically (e.g., daily via cron or background task).
    Returns summary of scheduled calls.
    """
    farmers = db.query(FarmerProfile).filter(FarmerProfile.total_calls > 0).all()
    stats = {"crop_reminders": 0, "weather_alerts": 0, "total_farmers": len(farmers)}

    for farmer in farmers:
        lang = farmer.preferred_language or "hi"
        name = farmer.name or "Kisan"

        # Crop-based reminders
        crop_reminders = generate_crop_reminders(db, farmer)
        for reminder in crop_reminders:
            template = TEMPLATES.get(reminder["type"], {}).get(lang, TEMPLATES[reminder["type"]]["en"])
            message = template.format(
                name=name,
                crop=reminder["crop"],
                action=reminder["action"],
                detail=reminder["detail"],
            )
            call = ScheduledCall(
                farmer_id=farmer.id,
                call_type=reminder["type"],
                title=f"{reminder['action']} - {reminder['crop']}",
                message=message,
                language=lang,
                phone_number=None,  # Looked up at delivery time
                scheduled_for=reminder["schedule"],
            )
            db.add(call)
            stats["crop_reminders"] += 1

        # Weather alerts
        weather_alerts = generate_weather_alerts_for_farmer(db, farmer)
        for alert in weather_alerts:
            template = TEMPLATES.get("weather_alert", {}).get(lang, TEMPLATES["weather_alert"]["en"])
            message = template.format(
                title=alert["title"],
                message=alert["message"][:200],
            )
            # Check if already sent
            existing = (
                db.query(ScheduledCall)
                .filter(
                    ScheduledCall.farmer_id == farmer.id,
                    ScheduledCall.title == alert["title"],
                    ScheduledCall.status == "sent",
                )
                .first()
            )
            if not existing:
                call = ScheduledCall(
                    farmer_id=farmer.id,
                    call_type="weather_alert",
                    title=alert["title"],
                    message=message,
                    language=lang,
                    scheduled_for=alert["schedule"],
                    priority=1 if alert.get("severity") == "critical" else 2,
                )
                db.add(call)
                stats["weather_alerts"] += 1

    db.commit()
    logger.info(f"Scheduled proactive calls: {stats}")
    return stats


def get_pending_calls(db: Session, limit: int = 50) -> list[ScheduledCall]:
    """Get calls ready to be sent."""
    now = datetime.now()
    return (
        db.query(ScheduledCall)
        .filter(
            ScheduledCall.status == "pending",
            ScheduledCall.scheduled_for <= now,
            ScheduledCall.attempts < 3,
        )
        .order_by(ScheduledCall.priority.asc(), ScheduledCall.scheduled_for.asc())
        .limit(limit)
        .all()
    )


def deliver_call(db: Session, call: ScheduledCall) -> str:
    """Deliver a scheduled call via Twilio voice or WhatsApp.
    Returns delivery status.
    """
    call.attempts += 1

    if not settings.TWILIO_ACCOUNT_SID or settings.MOCK_MODE:
        call.status = "sent"
        call.sent_at = datetime.now()
        db.commit()
        logger.info(f"[MOCK] Delivered call {call.id} to farmer {call.farmer_id}: {call.title}")
        return "mock_sent"

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        # Prefer WhatsApp, fallback to voice
        farmer = db.query(FarmerProfile).filter(FarmerProfile.id == call.farmer_id).first()
        if not farmer or not farmer.phone_hash:
            call.status = "failed"
            db.commit()
            return "no_phone"

        # Send via WhatsApp
        msg = client.messages.create(
            body=call.message,
            from_=f"whatsapp:{settings.TWILIO_PHONE_NUMBER}",
            to=f"whatsapp:{call.phone_number}" if call.phone_number else f"whatsapp:+91{farmer.phone_hash}",
        )
        call.status = "sent"
        call.sent_at = datetime.now()
        db.commit()
        logger.info(f"Delivered call {call.id} via WhatsApp: {msg.sid}")
        return "sent"

    except Exception as e:
        logger.error(f"Call delivery failed for {call.id}: {e}")
        if call.attempts >= 3:
            call.status = "failed"
        db.commit()
        return "failed"
