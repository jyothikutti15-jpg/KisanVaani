from sqlalchemy import Column, DateTime, Integer, String, Text, func

from app.database import Base


class WhatsAppMessage(Base):
    """Log of WhatsApp conversations."""
    __tablename__ = "whatsapp_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wa_message_id = Column(String, unique=True, nullable=True)
    farmer_phone = Column(String, index=True)
    farmer_id = Column(Integer, nullable=True, index=True)
    direction = Column(String)  # inbound, outbound
    message_type = Column(String, default="text")  # text, image, audio
    content = Column(Text)
    ai_response = Column(Text, nullable=True)
    language = Column(String, default="en")
    created_at = Column(DateTime, default=func.now())
