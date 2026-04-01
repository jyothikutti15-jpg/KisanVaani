import base64
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.services.voice_pipeline import log_call, process_text

router = APIRouter(prefix="/api/voice", tags=["voice"])

AUDIO_DIR = Path(settings.AUDIO_DIR)
AUDIO_DIR.mkdir(exist_ok=True)


class TextQuery(BaseModel):
    text: str
    language: str = "auto"
    session_id: str
    farmer_id: Optional[int] = None
    country: str = "IN"


class VoiceResponseSchema(BaseModel):
    transcript: str
    response_text: str
    audio_url: str
    language: str
    session_id: str
    expense_detected: Optional[dict] = None


@router.post("/text", response_model=VoiceResponseSchema)
async def process_text_input(body: TextQuery, db: Session = Depends(get_db)):
    """Text input with farmer memory and multi-country support."""
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
async def process_photo_diagnosis(
    photo: UploadFile = File(...),
    text: str = Form("Please diagnose this crop problem"),
    language: str = Form("en"),
    session_id: str = Form(...),
    farmer_id: Optional[int] = Form(None),
    country: str = Form("IN"),
    db: Session = Depends(get_db),
):
    """Photo diagnosis — upload a crop image for AI analysis."""
    photo_bytes = await photo.read()
    image_b64 = base64.b64encode(photo_bytes).decode("utf-8")

    # Detect media type
    content_type = photo.content_type or "image/jpeg"

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
    path = AUDIO_DIR / filename
    if not path.exists():
        return {"error": "Audio not found"}
    media_type = "audio/mpeg" if filename.endswith(".mp3") else "audio/wav"
    return FileResponse(path, media_type=media_type)
