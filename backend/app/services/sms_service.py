"""SMS Fallback Service — For farmers with zero internet access.

Enables two-way farming advice via basic SMS:
1. Farmer sends SMS question to KisanVaani number
2. System processes through AI pipeline
3. Response sent back as SMS (160-char chunks)

Also supports:
- Proactive SMS alerts (weather, price, reminders)
- SMS-based onboarding (REGISTER name crop region)
- SMS expense logging (EXPENSE 2000 urea wheat)
"""
import hashlib
import logging
import re
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.farmer import FarmerProfile
from app.services.llm_service import llm_service
from app.services.farming_knowledge import get_context
from app.services.voice_pipeline import add_to_history, get_history, log_call

logger = logging.getLogger("kisanvaani.sms")

# SMS commands
SMS_COMMANDS = {
    "REGISTER": "Register as a new farmer. Format: REGISTER <name> <crop> <region>",
    "PRICE": "Get current mandi price. Format: PRICE <crop>",
    "WEATHER": "Get weather forecast. Format: WEATHER <location>",
    "EXPENSE": "Log an expense. Format: EXPENSE <amount> <description> <crop>",
    "HELP": "Get list of available commands",
    "SCHEME": "Check government scheme eligibility. Format: SCHEME",
}

HELP_TEXT = """KisanVaani SMS Commands:
- Ask any farming question directly
- REGISTER name crop region
- PRICE tomato
- WEATHER pune
- EXPENSE 2000 urea wheat
- SCHEME
- HELP
Reply with your farming question for AI advice."""


def _detect_language_sms(text: str) -> str:
    """Detect language from SMS text."""
    for ch in text:
        if "\u0900" <= ch <= "\u097F":
            return "hi"
        if "\u0C00" <= ch <= "\u0C7F":
            return "te"
        if "\u0B80" <= ch <= "\u0BFF":
            return "ta"
    return "en"


def _truncate_for_sms(text: str, max_chars: int = 450) -> str:
    """Truncate AI response for SMS (keeping most useful part).
    Standard SMS is 160 chars, but concatenated SMS can be ~450.
    """
    # Remove markdown formatting
    text = re.sub(r'[#*_`]', '', text)
    text = re.sub(r'\n{2,}', '\n', text)
    text = text.strip()

    if len(text) <= max_chars:
        return text

    # Try to cut at sentence boundary
    truncated = text[:max_chars]
    last_period = truncated.rfind('.')
    last_pipe = truncated.rfind('|')
    cut_point = max(last_period, last_pipe)
    if cut_point > max_chars * 0.5:
        return truncated[:cut_point + 1]
    return truncated[:max_chars - 3] + "..."


def _get_or_create_farmer_sms(db: Session, phone: str) -> FarmerProfile:
    """Find or create farmer by phone hash."""
    phone_hash = hashlib.sha256(phone.encode()).hexdigest()[:16]
    farmer = db.query(FarmerProfile).filter(FarmerProfile.phone_hash == phone_hash).first()
    if not farmer:
        farmer = FarmerProfile(phone_hash=phone_hash, preferred_language="hi", country="IN")
        db.add(farmer)
        db.commit()
        db.refresh(farmer)
    return farmer


async def process_sms(
    db: Session,
    phone: str,
    message: str,
) -> str:
    """Process incoming SMS and return response text.

    Handles both commands (REGISTER, PRICE, WEATHER) and free-form questions.
    """
    message = message.strip()
    if not message:
        return HELP_TEXT

    upper = message.upper()
    farmer = _get_or_create_farmer_sms(db, phone)
    language = _detect_language_sms(message)

    # Command: HELP
    if upper == "HELP":
        return HELP_TEXT

    # Command: REGISTER <name> <crop> <region>
    if upper.startswith("REGISTER"):
        parts = message.split(maxsplit=3)
        if len(parts) >= 4:
            farmer.name = parts[1]
            farmer.crops = f'["{parts[2]}"]'
            farmer.region = parts[3]
            farmer.preferred_language = language
            db.commit()
            return f"Welcome {parts[1]}! Registered with crop: {parts[2]}, region: {parts[3]}. Now ask any farming question."
        return "Format: REGISTER <name> <crop> <region>. Example: REGISTER Ramesh Tomato Maharashtra"

    # Command: PRICE <crop>
    if upper.startswith("PRICE"):
        parts = message.split(maxsplit=1)
        crop = parts[1] if len(parts) > 1 else "wheat"
        try:
            from app.services.price_predictor import predict_price, _load_current_prices
            prices = _load_current_prices()
            for name, price in prices.items():
                if crop.lower() in name.lower():
                    return f"{name}: Rs {price}/quintal (current mandi rate). Send 'PRICE {crop}' anytime for updates."
            return f"Price for '{crop}' not found. Available: Wheat, Rice, Tomato, Onion, Cotton, Soybean"
        except Exception:
            return "Price service temporarily unavailable. Try again later."

    # Command: WEATHER <location>
    if upper.startswith("WEATHER"):
        parts = message.split(maxsplit=1)
        location = parts[1] if len(parts) > 1 else "pune"
        try:
            from app.services.weather_service import get_weather
            weather = await get_weather(location)
            if "error" in weather:
                return f"Weather not found for '{location}'. Try: Pune, Nagpur, Kakamega, Kano"
            curr = weather.get("current", {})
            fc = weather.get("forecast", [{}])[0]
            return (
                f"Weather {location}: {curr.get('temperature')}C, {curr.get('condition')}. "
                f"Tomorrow: {fc.get('temp_min')}-{fc.get('temp_max')}C, Rain: {fc.get('rain_chance')}%"
            )
        except Exception:
            return "Weather service temporarily unavailable."

    # Command: EXPENSE <amount> <description> <crop>
    if upper.startswith("EXPENSE"):
        parts = message.split(maxsplit=3)
        if len(parts) >= 3:
            try:
                amount = float(parts[1])
                desc = parts[2]
                crop = parts[3] if len(parts) > 3 else None
                from app.models.farmer import FarmerExpense
                expense = FarmerExpense(
                    farmer_id=farmer.id, category="other", description=desc,
                    amount=amount, crop=crop,
                )
                db.add(expense)
                db.commit()
                return f"Expense logged: Rs {amount} for {desc}" + (f" ({crop})" if crop else "") + ". Total tracked by KisanVaani."
            except ValueError:
                pass
        return "Format: EXPENSE <amount> <description> <crop>. Example: EXPENSE 2000 urea wheat"

    # Command: SCHEME
    if upper.startswith("SCHEME"):
        country = farmer.country or "IN"
        if country == "IN":
            return (
                "Schemes for you: 1) KCC loan Rs 3L at 4% - apply at bank. "
                "2) PM-KISAN Rs 6000/yr free - pmkisan.gov.in. "
                "3) PMFBY crop insurance - 2% premium. "
                "Call KisanVaani for details."
            )
        elif country == "KE":
            return "Kenya schemes: 1) AFC loans up to KES 5M. 2) NARIGP support. Contact county agriculture office."
        return "Send SCHEME to check government farming schemes available for you."

    # Free-form farming question -> AI pipeline
    session_id = f"sms_{farmer.phone_hash}"
    context = get_context(language=language, country=farmer.country or "IN")
    history = get_history(session_id, db)

    response = await llm_service.advise(
        question=message,
        language=language,
        context=context,
        history=history,
    )
    clean = llm_service.clean_response(response)

    # Check for expense in AI response
    expense_data = llm_service.extract_expense(response)
    if expense_data:
        from app.models.farmer import FarmerExpense
        exp = FarmerExpense(
            farmer_id=farmer.id,
            category=expense_data.get("category", "other"),
            description=expense_data.get("description", ""),
            amount=expense_data.get("amount", 0),
            crop=expense_data.get("crop"),
        )
        db.add(exp)

    # Update farmer
    farmer.total_calls = (farmer.total_calls or 0) + 1
    farmer.last_advice = clean[:500]
    add_to_history(session_id, message, clean, db)
    log_call(db, session_id, "sms", message, clean, language, phone=phone)

    return _truncate_for_sms(clean)


async def send_sms(phone: str, message: str) -> dict:
    """Send SMS via Twilio."""
    if settings.MOCK_MODE or not settings.TWILIO_ACCOUNT_SID:
        logger.info(f"[MOCK SMS] To {phone[:6]}***: {message[:80]}...")
        return {"status": "mock", "message": message}

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone,
        )
        logger.info(f"SMS sent to {phone[:6]}***: {msg.sid}")
        return {"status": "sent", "sid": msg.sid}
    except Exception as e:
        logger.error(f"SMS send failed: {e}")
        return {"status": "error", "detail": str(e)}
