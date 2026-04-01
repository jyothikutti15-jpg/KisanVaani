import struct
import urllib.parse
import urllib.request
import wave
from io import BytesIO

from app.config import SUPPORTED_LANGUAGES, settings


def _generate_silence_wav(duration_seconds: float = 2.0, sample_rate: int = 24000) -> bytes:
    """Generate a silent WAV file for mock mode."""
    num_samples = int(sample_rate * duration_seconds)
    buf = BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{num_samples}h", *([0] * num_samples)))
    return buf.getvalue()


MOCK_AUDIO = _generate_silence_wav(2.0)

# Language code mapping for Google Translate TTS
GTTS_LANG_MAP = {
    "hi": "hi", "te": "te", "ta": "ta", "sw": "sw", "en": "en",
}


class TTSService:
    """Text-to-speech using Google Translate TTS (free, no API key needed).

    For production, the frontend also uses the browser's SpeechSynthesis API
    as a primary TTS method (zero cost, instant). This backend TTS is used
    for Twilio phone calls and as a fallback.
    """

    async def synthesize(self, text: str, language: str = "en") -> bytes:
        if settings.MOCK_MODE:
            return MOCK_AUDIO

        # Use Google Translate TTS (free, no key needed, supports all our languages)
        lang_code = GTTS_LANG_MAP.get(language, "en")

        # Split text into chunks of ~200 chars (Google TTS limit)
        chunks = self._split_text(text, 200)
        audio_parts = []

        for chunk in chunks:
            encoded = urllib.parse.quote(chunk)
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl={lang_code}&q={encoded}"

            try:
                req = urllib.request.Request(url)
                req.add_header("User-Agent", "Mozilla/5.0")
                with urllib.request.urlopen(req, timeout=10) as resp:
                    audio_parts.append(resp.read())
            except Exception:
                continue

        if audio_parts:
            return b"".join(audio_parts)
        return MOCK_AUDIO

    def _split_text(self, text: str, max_len: int) -> list[str]:
        """Split text at sentence boundaries."""
        if len(text) <= max_len:
            return [text]
        chunks = []
        current = ""
        for sentence in text.replace("।", ".").split("."):
            sentence = sentence.strip()
            if not sentence:
                continue
            if len(current) + len(sentence) + 2 <= max_len:
                current = f"{current}. {sentence}" if current else sentence
            else:
                if current:
                    chunks.append(current + ".")
                current = sentence
        if current:
            chunks.append(current + ".")
        return chunks or [text[:max_len]]

    def get_voice_config(self, language: str) -> dict:
        return SUPPORTED_LANGUAGES.get(language, SUPPORTED_LANGUAGES["en"])


tts_service = TTSService()
