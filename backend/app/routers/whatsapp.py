"""WhatsApp integration via Twilio WhatsApp Business API.

Farmers can send text, voice notes, and photos via WhatsApp.
Supports the same AI pipeline as voice calls and web demo.
"""
import base64
import hashlib
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.farmer import FarmerProfile
from app.models.whatsapp import WhatsAppMessage
from app.services.llm_service import llm_service
from app.services.voice_pipeline import add_to_history, get_history, log_call

logger = logging.getLogger("kisanvaani.whatsapp")
router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])


def _detect_language(text: str) -> str:
    """Simple language detection based on script."""
    for ch in text:
        if "\u0900" <= ch <= "\u097F":
            return "hi"
        if "\u0C00" <= ch <= "\u0C7F":
            return "te"
        if "\u0B80" <= ch <= "\u0BFF":
            return "ta"
    # Swahili detection: common words
    swahili_words = {"habari", "shamba", "mimi", "nini", "yangu", "mimea", "mahindi", "maji"}
    if any(w in text.lower().split() for w in swahili_words):
        return "sw"
    return "en"


def _get_or_create_farmer(db: Session, phone: str, language: str) -> FarmerProfile:
    """Find farmer by phone hash or create a new profile."""
    phone_hash = hashlib.sha256(phone.encode()).hexdigest()[:16]
    farmer = db.query(FarmerProfile).filter(FarmerProfile.phone_hash == phone_hash).first()
    if not farmer:
        farmer = FarmerProfile(
            phone_hash=phone_hash,
            preferred_language=language,
            country="IN",
        )
        db.add(farmer)
        db.commit()
        db.refresh(farmer)
        logger.info(f"New WhatsApp farmer created: id={farmer.id}")
    return farmer


@router.post("/webhook")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle incoming WhatsApp messages from Twilio.

    Twilio sends form data with:
    - Body: text message content
    - From: sender's WhatsApp number (whatsapp:+91XXXXXXXXXX)
    - To: your Twilio WhatsApp number
    - NumMedia: number of media attachments
    - MediaUrl0: URL of first media attachment
    - MediaContentType0: MIME type of first media
    """
    form = await request.form()
    body = form.get("Body", "").strip()
    sender = form.get("From", "")
    num_media = int(form.get("NumMedia", "0"))
    media_url = form.get("MediaUrl0")
    media_type = form.get("MediaContentType0", "")

    phone = sender.replace("whatsapp:", "")
    logger.info(f"WhatsApp message from {phone[:6]}***: text={len(body)} chars, media={num_media}")

    # Detect language
    language = _detect_language(body) if body else "en"

    # Get/create farmer
    farmer = _get_or_create_farmer(db, phone, language)
    session_id = f"wa_{farmer.phone_hash}"

    # Handle image messages (photo diagnosis)
    image_data = None
    image_media_type = "image/jpeg"
    if num_media > 0 and media_url and media_type.startswith("image/"):
        try:
            import urllib.request
            req = urllib.request.Request(media_url)
            if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
                credentials = base64.b64encode(
                    f"{settings.TWILIO_ACCOUNT_SID}:{settings.TWILIO_AUTH_TOKEN}".encode()
                ).decode()
                req.add_header("Authorization", f"Basic {credentials}")
            with urllib.request.urlopen(req, timeout=15) as resp:
                image_bytes = resp.read()
                image_data = base64.b64encode(image_bytes).decode("utf-8")
                image_media_type = media_type
            if not body:
                body = "Please diagnose this crop problem from the photo"
            logger.info(f"Photo received: {len(image_bytes)//1024}KB, type={media_type}")
        except Exception as e:
            logger.warning(f"Failed to download WhatsApp media: {e}")

    if not body:
        body = "Hello"

    # Build farming context
    from app.services.farming_knowledge import get_context
    context = get_context(language=language, country=farmer.country or "IN")

    # Get conversation history
    history = get_history(session_id, db)

    # Get AI response
    response_text = await llm_service.advise(
        question=body,
        language=language,
        context=context,
        history=history,
        image_data=image_data,
        image_media_type=image_media_type,
    )
    clean_response = llm_service.clean_response(response_text)

    # Check for expense
    expense_data = llm_service.extract_expense(response_text)
    if expense_data:
        from app.models.farmer import FarmerExpense
        expense = FarmerExpense(
            farmer_id=farmer.id,
            category=expense_data.get("category", "other"),
            description=expense_data.get("description", ""),
            amount=expense_data.get("amount", 0),
            crop=expense_data.get("crop"),
        )
        db.add(expense)

    # Update conversation history
    add_to_history(session_id, body, clean_response, db)

    # Log message
    msg = WhatsAppMessage(
        farmer_phone=phone,
        farmer_id=farmer.id,
        direction="inbound",
        message_type="image" if image_data else "text",
        content=body,
        ai_response=clean_response,
        language=language,
    )
    db.add(msg)

    # Update farmer stats
    farmer.total_calls = (farmer.total_calls or 0) + 1
    farmer.last_advice = clean_response[:500]
    farmer.preferred_language = language
    db.commit()

    # Log to call log (unified analytics)
    log_call(db, session_id, "whatsapp", body, clean_response, language, phone=phone)

    # Return TwiML response
    safe_response = clean_response.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{safe_response}</Message>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@router.get("/webhook")
async def whatsapp_verify(request: Request):
    """Twilio webhook verification (GET request)."""
    return Response(content="OK", media_type="text/plain")


class SendMessageRequest(BaseModel):
    to: str  # Phone number with country code
    message: str
    language: str = "en"


@router.post("/send")
async def send_whatsapp_message(body: SendMessageRequest, db: Session = Depends(get_db)):
    """Send outbound WhatsApp message to a farmer.
    Used for proactive alerts, reminders, and follow-ups.
    """
    if settings.MOCK_MODE or not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN or not settings.TWILIO_PHONE_NUMBER:
        return {"status": "mock", "message": "WhatsApp sending disabled (mock mode or no Twilio credentials)"}

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=body.message,
            from_=f"whatsapp:{settings.TWILIO_PHONE_NUMBER}",
            to=f"whatsapp:{body.to}",
        )

        # Log outbound message
        wa_msg = WhatsAppMessage(
            wa_message_id=msg.sid,
            farmer_phone=body.to,
            direction="outbound",
            content=body.message,
            language=body.language,
        )
        db.add(wa_msg)
        db.commit()

        logger.info(f"WhatsApp sent to {body.to[:6]}***: sid={msg.sid}")
        return {"status": "sent", "sid": msg.sid}

    except Exception as e:
        logger.error(f"WhatsApp send failed: {e}")
        return {"status": "error", "detail": str(e)}


@router.get("/conversations/{farmer_id}")
async def get_conversations(farmer_id: int, limit: int = 50, db: Session = Depends(get_db)):
    """Get WhatsApp conversation history for a farmer."""
    messages = (
        db.query(WhatsAppMessage)
        .filter(WhatsAppMessage.farmer_id == farmer_id)
        .order_by(WhatsAppMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": m.id,
            "direction": m.direction,
            "type": m.message_type,
            "content": m.content,
            "ai_response": m.ai_response,
            "language": m.language,
            "created_at": str(m.created_at),
        }
        for m in reversed(messages)
    ]
