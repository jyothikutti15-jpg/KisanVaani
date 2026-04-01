from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func

from app.database import Base


class FarmerProfile(Base):
    """Enhanced farmer profile with memory — remembers across calls."""
    __tablename__ = "farmer_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_hash = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=True)
    preferred_language = Column(String, default="hi")
    country = Column(String, default="IN")  # IN, KE, NG, ET
    region = Column(String, nullable=True)   # State/county
    district = Column(String, nullable=True)
    village = Column(String, nullable=True)

    # Farm details
    land_size_acres = Column(Float, nullable=True)
    crops = Column(Text, nullable=True)          # JSON: ["rice", "cotton", "tomato"]
    soil_type = Column(String, nullable=True)    # clay, sandy, loam, black
    irrigation_type = Column(String, nullable=True)  # rainfed, borewell, canal, drip

    # History summary (updated by AI after each call)
    past_problems = Column(Text, nullable=True)  # JSON: ["bollworm_cotton_2026", "leaf_blight_tomato_2026"]
    active_issues = Column(Text, nullable=True)  # JSON: current ongoing problems
    last_advice = Column(Text, nullable=True)     # Last AI advice given

    # Stats
    total_calls = Column(Integer, default=0)
    first_call = Column(DateTime, default=func.now())
    last_call = Column(DateTime, default=func.now(), onupdate=func.now())


class FarmerExpense(Base):
    """Voice-tracked farm expenses."""
    __tablename__ = "farmer_expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    farmer_id = Column(Integer, index=True)
    category = Column(String)       # seeds, fertilizer, pesticide, labor, irrigation, equipment, transport
    description = Column(Text)
    amount = Column(Float)
    date = Column(String, nullable=True)
    crop = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
