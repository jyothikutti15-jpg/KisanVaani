from dataclasses import dataclass
from typing import Optional

from app.config import settings


@dataclass
class TranscriptionResult:
    text: str
    language: str
    confidence: float = 0.95


# Mock responses for testing without API keys
MOCK_RESPONSES = {
    "hi": TranscriptionResult(
        text="Mere tamatar ke patte peele ho rahe hain, kya karoon?",
        language="hi",
    ),
    "te": TranscriptionResult(
        text="Naa vari pantalo purugulu vasthunnaayi, em cheyali?",
        language="te",
    ),
    "en": TranscriptionResult(
        text="My cotton plants have white spots on the leaves, what should I do?",
        language="en",
    ),
    "sw": TranscriptionResult(
        text="Mimea yangu ya mahindi yana wadudu, nifanye nini?",
        language="sw",
    ),
    "ta": TranscriptionResult(
        text="En nel payiril puzhu thakkam irukku, enna seyya vendum?",
        language="ta",
    ),
}


class STTService:
    """Speech-to-text service.

    In production, STT is handled by the browser's Web Speech API (free, no key needed).
    The frontend sends transcribed text directly via /api/voice/text.
    This service is only used as fallback for audio file uploads.
    """

    async def transcribe(
        self,
        audio_bytes: bytes,
        audio_format: str = "webm",
        language_hint: Optional[str] = None,
    ) -> TranscriptionResult:
        # Browser handles STT via Web Speech API — this is the mock fallback
        lang = language_hint or "hi"
        return MOCK_RESPONSES.get(lang, MOCK_RESPONSES["en"])


stt_service = STTService()
