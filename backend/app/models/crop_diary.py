from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func

from app.database import Base


class CropDiaryEntry(Base):
    """Voice-based crop diary — tracks planting, activities, and generates reminders."""
    __tablename__ = "crop_diary"

    id = Column(Integer, primary_key=True, autoincrement=True)
    farmer_id = Column(Integer, index=True)
    crop = Column(String)
    activity = Column(String)  # planted, irrigated, fertilized, sprayed, harvested, weeded, sold
    details = Column(Text, nullable=True)
    quantity = Column(String, nullable=True)  # "5 kg seeds", "2 acres"
    date_recorded = Column(String)  # YYYY-MM-DD
    days_since_planting = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())


class CropReminder(Base):
    """Auto-generated reminders based on crop diary."""
    __tablename__ = "crop_reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    farmer_id = Column(Integer, index=True)
    crop = Column(String)
    reminder_type = Column(String)  # irrigation, fertilizer, pest_check, harvest
    message = Column(Text)
    due_date = Column(String)
    completed = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
