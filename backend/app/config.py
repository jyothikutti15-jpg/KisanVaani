from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    DATABASE_URL: str = "sqlite:///./kisanvaani.db"
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    MOCK_MODE: bool = True  # Set False when API keys are configured
    AUDIO_DIR: str = str(Path(__file__).parent.parent / "audio_cache")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()

SUPPORTED_LANGUAGES = {
    "hi": {
        "name": "Hindi",
        "native_name": "हिन्दी",
        "tts_voice": "hi-IN-Wavenet-A",
        "tts_language_code": "hi-IN",
        "greeting": "KisanVaani mein aapka swagat hai. Apna sawaal poochiye.",
    },
    "te": {
        "name": "Telugu",
        "native_name": "తెలుగు",
        "tts_voice": "te-IN-Standard-A",
        "tts_language_code": "te-IN",
        "greeting": "KisanVaani ki swagatham. Mee prashna adagandi.",
    },
    "ta": {
        "name": "Tamil",
        "native_name": "தமிழ்",
        "tts_voice": "ta-IN-Wavenet-A",
        "tts_language_code": "ta-IN",
        "greeting": "KisanVaani kku varavergkirom. Ungal kelvi keelungal.",
    },
    "sw": {
        "name": "Swahili",
        "native_name": "Kiswahili",
        "tts_voice": "sw-KE-Standard-A",
        "tts_language_code": "sw-KE",
        "greeting": "Karibu KisanVaani. Uliza swali lako.",
    },
    "en": {
        "name": "English",
        "native_name": "English",
        "tts_voice": "en-IN-Wavenet-A",
        "tts_language_code": "en-IN",
        "greeting": "Welcome to KisanVaani. Please ask your farming question.",
    },
}
