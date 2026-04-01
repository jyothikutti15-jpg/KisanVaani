from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func

from app.database import Base


class CallLog(Base):
    __tablename__ = "call_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, index=True)
    source = Column(String)  # "phone" or "web"
    phone_number = Column(String, nullable=True)
    language = Column(String, default="hi")
    farmer_question = Column(Text)
    ai_response = Column(Text)
    duration_seconds = Column(Float, nullable=True)
    category = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
