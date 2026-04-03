"""Market index model for TAIEX daily data."""
from sqlalchemy import Column, Integer, Date, DECIMAL, UniqueConstraint
from app.database import Base
from app.models.base import TimestampMixin


class MarketIndex(Base, TimestampMixin):
    """TAIEX market index daily OHLCV data."""

    __tablename__ = "market_indices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    open = Column(DECIMAL(10, 2), nullable=False)
    high = Column(DECIMAL(10, 2), nullable=False)
    low = Column(DECIMAL(10, 2), nullable=False)
    close = Column(DECIMAL(10, 2), nullable=False)
    volume = Column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint('date', name='uix_market_index_date'),
    )

    def __repr__(self) -> str:
        return f"<MarketIndex {self.date} close={self.close}>"
