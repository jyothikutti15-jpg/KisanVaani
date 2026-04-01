from sqlalchemy import Column, DateTime, Integer, String, Text, func

from app.database import Base


class Alert(Base):
    """Proactive alerts sent to farmers."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String)       # weather, pest_outbreak, price_spike, scheme_deadline
    severity = Column(String)         # critical, warning, info
    title = Column(String)
    message = Column(Text)
    country = Column(String, default="IN")
    region = Column(String, nullable=True)
    affected_crops = Column(Text, nullable=True)  # JSON array
    source = Column(String, nullable=True)        # IMD, NPSS, mandi, manual
    active = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)


class CommunityInsight(Base):
    """Aggregated community intelligence from farmer questions."""
    __tablename__ = "community_insights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    region = Column(String, index=True)
    country = Column(String, default="IN")
    topic = Column(String)            # pest name, disease, crop issue
    affected_crop = Column(String, nullable=True)
    farmer_count = Column(Integer, default=1)
    first_reported = Column(DateTime, default=func.now())
    last_reported = Column(DateTime, default=func.now())
    trending = Column(Integer, default=0)  # 1 if rapidly increasing
    ai_summary = Column(Text, nullable=True)  # AI-generated summary of the trend
