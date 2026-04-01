import json
import time
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session

from app.models.call import CallLog
from app.models.farmer import FarmerExpense, FarmerProfile
from app.services.farming_knowledge import get_context
from app.services.llm_service import llm_service
from app.services.stt_service import stt_service
from app.services.tts_service import tts_service


@dataclass
class PipelineResult:
    transcript: str
    response_text: str
    audio: bytes
    language: str
    duration: float
    expense_detected: Optional[dict] = None


# In-memory conversation history
_sessions: dict[str, list[dict]] = {}


def get_history(session_id: str) -> list[dict]:
    return _sessions.get(session_id, [])


def add_to_history(session_id: str, farmer: str, advisor: str):
    if session_id not in _sessions:
        _sessions[session_id] = []
    _sessions[session_id].append({"farmer": farmer, "advisor": advisor})
    if len(_sessions[session_id]) > 4:
        _sessions[session_id] = _sessions[session_id][-4:]


def _get_farmer_context(db: Session, farmer_id: Optional[int], country: str, language: str) -> tuple[str, Optional[FarmerProfile]]:
    """Build context with farmer memory if farmer_id is provided."""
    farmer = None
    farmer_dict = None

    if farmer_id:
        farmer = db.query(FarmerProfile).filter(FarmerProfile.id == farmer_id).first()
        if farmer:
            farmer_dict = {
                "name": farmer.name,
                "region": farmer.region,
                "district": farmer.district,
                "village": farmer.village,
                "crops": farmer.crops,
                "land_size_acres": farmer.land_size_acres,
                "soil_type": farmer.soil_type,
                "irrigation_type": farmer.irrigation_type,
                "past_problems": farmer.past_problems,
                "active_issues": farmer.active_issues,
                "last_advice": farmer.last_advice,
            }
            country = farmer.country or country

    context = get_context(language=language, country=country, farmer_profile=farmer_dict)
    return context, farmer


async def process_text(
    text: str,
    language: str,
    session_id: str,
    db: Optional[Session] = None,
    farmer_id: Optional[int] = None,
    country: str = "IN",
    image_data: Optional[str] = None,
    image_media_type: str = "image/jpeg",
) -> PipelineResult:
    """Enhanced pipeline with farmer memory, photo diagnosis, and expense tracking."""
    start = time.time()

    # Get context with farmer memory
    farmer = None
    if db and farmer_id:
        context, farmer = _get_farmer_context(db, farmer_id, country, language)
    else:
        context = get_context(language=language, country=country)

    # LLM reasoning (with optional image)
    history = get_history(session_id)
    response_text = await llm_service.advise(
        question=text,
        language=language,
        context=context,
        history=history,
        image_data=image_data,
        image_media_type=image_media_type,
    )

    # Extract expense if detected
    expense_data = llm_service.extract_expense(response_text)
    clean_response = llm_service.clean_response(response_text)

    # Save expense if detected and farmer exists
    if expense_data and db and farmer_id:
        expense = FarmerExpense(
            farmer_id=farmer_id,
            category=expense_data.get("category", "other"),
            description=expense_data.get("description", ""),
            amount=expense_data.get("amount", 0),
            crop=expense_data.get("crop"),
        )
        db.add(expense)

    # Update farmer memory
    if farmer and db:
        farmer.total_calls = (farmer.total_calls or 0) + 1
        farmer.last_advice = clean_response[:500]
        db.commit()

    # TTS
    audio = await tts_service.synthesize(clean_response, language)
    add_to_history(session_id, text, clean_response)

    # Log call
    if db:
        log_call(db, session_id, "web", text, clean_response, language)

    return PipelineResult(
        transcript=text,
        response_text=clean_response,
        audio=audio,
        language=language,
        duration=time.time() - start,
        expense_detected=expense_data,
    )


async def process_audio(
    audio_bytes: bytes,
    session_id: str,
    language_hint: Optional[str] = None,
    audio_format: str = "webm",
) -> PipelineResult:
    """Audio pipeline (fallback — browser usually handles STT)."""
    start = time.time()
    transcription = await stt_service.transcribe(audio_bytes, audio_format, language_hint)
    history = get_history(session_id)
    response_text = await llm_service.advise(
        question=transcription.text, language=transcription.language, history=history
    )
    clean_response = llm_service.clean_response(response_text)
    audio = await tts_service.synthesize(clean_response, transcription.language)
    add_to_history(session_id, transcription.text, clean_response)

    return PipelineResult(
        transcript=transcription.text, response_text=clean_response,
        audio=audio, language=transcription.language, duration=time.time() - start,
    )


def log_call(db: Session, session_id: str, source: str, question: str,
             response: str, language: str, phone: Optional[str] = None):
    log = CallLog(
        session_id=session_id, source=source, phone_number=phone,
        language=language, farmer_question=question, ai_response=response,
    )
    db.add(log)
    db.commit()
