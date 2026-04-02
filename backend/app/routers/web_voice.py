import base64
import logging
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.services.voice_pipeline import log_call, process_text

logger = logging.getLogger("kisanvaani.voice")
router = APIRouter(prefix="/api/voice", tags=["voice"])
limiter = Limiter(key_func=get_remote_address)

AUDIO_DIR = Path(settings.AUDIO_DIR)
AUDIO_DIR.mkdir(exist_ok=True)

ALLOWED_LANGUAGES = {"hi", "te", "ta", "sw", "en", "auto"}
MAX_PHOTO_SIZE = 10 * 1024 * 1024  # 10MB


class TextQuery(BaseModel):
    text: str
    language: str = "auto"
    session_id: str
    farmer_id: Optional[int] = None
    country: str = "IN"

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Text cannot be empty")
        if len(v) > settings.MAX_INPUT_LENGTH:
            raise ValueError(f"Text exceeds maximum length of {settings.MAX_INPUT_LENGTH} characters")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in ALLOWED_LANGUAGES:
            raise ValueError(f"Unsupported language: {v}. Supported: {ALLOWED_LANGUAGES}")
        return v

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        if len(v) > 100:
            raise ValueError("Session ID too long")
        return v


class VoiceResponseSchema(BaseModel):
    transcript: str
    response_text: str
    audio_url: str
    language: str
    session_id: str
    expense_detected: Optional[dict] = None


@router.post("/text", response_model=VoiceResponseSchema)
@limiter.limit("20/minute")
async def process_text_input(request: Request, body: TextQuery, db: Session = Depends(get_db)):
    """Text input with farmer memory and multi-country support."""
    logger.info(f"Text query: lang={body.language}, session={body.session_id[:20]}..., len={len(body.text)}")

    result = await process_text(
        text=body.text,
        language=body.language if body.language != "auto" else "en",
        session_id=body.session_id,
        db=db,
        farmer_id=body.farmer_id,
        country=body.country,
    )

    audio_filename = f"{body.session_id}_{uuid4().hex[:8]}.wav"
    audio_path = AUDIO_DIR / audio_filename
    with open(audio_path, "wb") as f:
        f.write(result.audio)

    return VoiceResponseSchema(
        transcript=result.transcript,
        response_text=result.response_text,
        audio_url=f"/api/voice/audio/{audio_filename}",
        language=result.language,
        session_id=body.session_id,
        expense_detected=result.expense_detected,
    )


@router.post("/photo", response_model=VoiceResponseSchema)
@limiter.limit("10/minute")
async def process_photo_diagnosis(
    request: Request,
    photo: UploadFile = File(...),
    text: str = Form("Please diagnose this crop problem"),
    language: str = Form("en"),
    session_id: str = Form(...),
    farmer_id: Optional[int] = Form(None),
    country: str = Form("IN"),
    db: Session = Depends(get_db),
):
    """Photo diagnosis — upload a crop image for AI analysis."""
    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/heic"}
    if photo.content_type and photo.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported image type: {photo.content_type}")

    # Validate text length
    if len(text) > settings.MAX_INPUT_LENGTH:
        raise HTTPException(status_code=400, detail="Text too long")

    photo_bytes = await photo.read()

    # Validate file size
    if len(photo_bytes) > MAX_PHOTO_SIZE:
        raise HTTPException(status_code=400, detail="Image too large (max 10MB)")

    image_b64 = base64.b64encode(photo_bytes).decode("utf-8")
    content_type = photo.content_type or "image/jpeg"

    logger.info(f"Photo diagnosis: lang={language}, size={len(photo_bytes)//1024}KB")

    result = await process_text(
        text=text,
        language=language,
        session_id=session_id,
        db=db,
        farmer_id=farmer_id,
        country=country,
        image_data=image_b64,
        image_media_type=content_type,
    )

    audio_filename = f"{session_id}_{uuid4().hex[:8]}.wav"
    audio_path = AUDIO_DIR / audio_filename
    with open(audio_path, "wb") as f:
        f.write(result.audio)

    return VoiceResponseSchema(
        transcript=result.transcript,
        response_text=result.response_text,
        audio_url=f"/api/voice/audio/{audio_filename}",
        language=result.language,
        session_id=session_id,
        expense_detected=result.expense_detected,
    )


@router.get("/audio/{filename}")
async def get_audio(filename: str):
    """Serve generated audio files."""
    # Sanitize filename to prevent path traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    path = AUDIO_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio not found")
    media_type = "audio/mpeg" if filename.endswith(".mp3") else "audio/wav"
    return FileResponse(path, media_type=media_type)
