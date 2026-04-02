import json

from sqlalchemy import Column, DateTime, Integer, String, Text, func

from app.database import Base


class ConversationTurn(Base):
    """Persistent conversation history (replaces in-memory sessions)."""
    __tablename__ = "conversation_turns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), index=True, nullable=False)
    turn_number = Column(Integer, nullable=False)
    farmer_text = Column(Text, nullable=False)
    advisor_text = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
