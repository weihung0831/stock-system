"""Sector tag model for industry grouping."""
from sqlalchemy import Column, Integer, String
from app.database import Base
from app.models.base import TimestampMixin


class SectorTag(Base, TimestampMixin):
    """User-defined sector tags for filtering stocks by industry."""

    __tablename__ = "sector_tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), unique=True, nullable=False)
    color = Column(String(7), nullable=False, default="#9ca3af")
    keywords = Column(String(200), nullable=False, default="")
    sort_order = Column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return f"<SectorTag {self.name}>"
