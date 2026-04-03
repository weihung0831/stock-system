"""System-wide settings model (single-row table)."""
from sqlalchemy import Column, Integer, Float, String, Text
from app.database import Base
from app.models.base import TimestampMixin


class SystemSetting(Base, TimestampMixin):
    """Single-row table storing system-wide screening settings."""

    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, default=1)
    chip_weight = Column(Float, nullable=False, default=40)
    fundamental_weight = Column(Float, nullable=False, default=35)
    technical_weight = Column(Float, nullable=False, default=25)
    screening_threshold = Column(Float, nullable=False, default=2.5)
    scheduler_enabled = Column(Integer, nullable=False, default=1)  # 1=enabled, 0=disabled
    scheduler_hour = Column(Integer, nullable=False, default=16)
    scheduler_minute = Column(Integer, nullable=False, default=30)
    top_sectors_json = Column(Text, nullable=True)  # JSON string of ranked sectors
