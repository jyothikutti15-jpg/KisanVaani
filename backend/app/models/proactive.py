from sqlalchemy import Column, DateTime, Integer, String, Text, func

from app.database import Base


class ScheduledCall(Base):
    """Proactive outbound calls scheduled for farmers."""
    __tablename__ = "scheduled_calls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    farmer_id = Column(Integer, index=True)
    call_type = Column(String)  # crop_reminder, weather_alert, price_alert, weekly_tip, scheme_deadline
    title = Column(String)
    message = Column(Text)
    language = Column(String, default="hi")
    phone_number = Column(String, nullable=True)
    scheduled_for = Column(DateTime)
    status = Column(String, default="pending")  # pending, sent, delivered, failed, cancelled
    priority = Column(Integer, default=2)  # 1=urgent, 2=normal, 3=low
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    sent_at = Column(DateTime, nullable=True)


class PriceHistory(Base):
    """Historical mandi price records for prediction."""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    crop = Column(String, index=True)
    market = Column(String, default="national")  # national, pune, bangalore, etc.
    price_per_quintal = Column(Integer)
    country = Column(String, default="IN")
    recorded_date = Column(String)  # YYYY-MM-DD
    created_at = Column(DateTime, default=func.now())
