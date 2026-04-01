from typing import Optional

from pydantic import BaseModel


class TextQuery(BaseModel):
    text: str
    language: str = "auto"
    session_id: str


class VoiceResponse(BaseModel):
    transcript: str
    response_text: str
    audio_url: str
    language: str
    session_id: str


class CallLogResponse(BaseModel):
    id: int
    session_id: str
    source: str
    phone_number: Optional[str] = None
    language: str
    farmer_question: str
    ai_response: str
    category: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}


class AnalyticsOverview(BaseModel):
    total_calls: int
    unique_sessions: int
    languages_served: int
    calls_today: int


class LanguageStat(BaseModel):
    language: str
    language_name: str
    count: int
    percentage: float


class DailyCallStat(BaseModel):
    date: str
    count: int
