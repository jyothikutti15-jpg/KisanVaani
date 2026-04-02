from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func

from app.database import Base


class ExpertCallback(Base):
    """Queue for human expert callbacks when AI confidence is low."""
    __tablename__ = "expert_callbacks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    farmer_id = Column(Integer, index=True)
    farmer_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    language = Column(String, default="hi")
    question = Column(Text)
    ai_response = Column(Text, nullable=True)  # What AI attempted
    ai_confidence = Column(String, nullable=True)  # low, uncertain
    reason = Column(String, nullable=True)  # why escalated
    category = Column(String, nullable=True)  # pest, disease, soil, livestock, legal
    region = Column(String, nullable=True)
    country = Column(String, default="IN")
    status = Column(String, default="pending")  # pending, assigned, resolved, expired
    assigned_expert = Column(String, nullable=True)
    expert_response = Column(Text, nullable=True)
    priority = Column(Integer, default=2)  # 1=urgent, 2=normal, 3=low
    created_at = Column(DateTime, default=func.now())
    resolved_at = Column(DateTime, nullable=True)


class FarmerQuestion(Base):
    """Anonymized farmer Q&A for peer sharing network."""
    __tablename__ = "farmer_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    region = Column(String, index=True)
    country = Column(String, default="IN")
    crop = Column(String, nullable=True)
    question_summary = Column(Text)  # Anonymized question
    ai_answer = Column(Text)
    category = Column(String, nullable=True)  # pest, disease, fertilizer, weather, market
    helpful_count = Column(Integer, default=0)
    language = Column(String, default="hi")
    created_at = Column(DateTime, default=func.now())


class MarketListing(Base):
    """Farmer marketplace — buy/sell crop produce."""
    __tablename__ = "market_listings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    farmer_id = Column(Integer, index=True)
    farmer_name = Column(String, nullable=True)
    listing_type = Column(String)  # sell, buy
    crop = Column(String, index=True)
    quantity = Column(String)  # "5 quintals", "200 kg"
    price_per_unit = Column(Float, nullable=True)  # Expected price
    unit = Column(String, default="quintal")
    region = Column(String, index=True)
    district = Column(String, nullable=True)
    country = Column(String, default="IN")
    phone_number = Column(String, nullable=True)  # Contact
    description = Column(Text, nullable=True)
    status = Column(String, default="active")  # active, sold, expired
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)


class SatelliteReport(Base):
    """Satellite-based crop health reports (NDVI analysis)."""
    __tablename__ = "satellite_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    farmer_id = Column(Integer, index=True, nullable=True)
    latitude = Column(Float)
    longitude = Column(Float)
    ndvi_score = Column(Float)  # -1 to 1 (>0.6 healthy, <0.3 stressed)
    health_status = Column(String)  # healthy, moderate, stressed, critical
    analysis = Column(Text)  # AI-generated interpretation
    crop = Column(String, nullable=True)
    region = Column(String, nullable=True)
    country = Column(String, default="IN")
    satellite_date = Column(String)  # Date of satellite image
    created_at = Column(DateTime, default=func.now())
