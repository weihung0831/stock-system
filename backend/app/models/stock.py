"""Stock model for basic stock information."""
from sqlalchemy import Column, Integer, String, Date, DECIMAL, Index
from app.database import Base
from app.models.base import TimestampMixin


class Stock(Base, TimestampMixin):
    """Stock master data table."""

    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(String(10), unique=True, nullable=False, index=True)
    stock_name = Column(String(50), nullable=False)
    market = Column(String(10), nullable=False)  # 'TWSE' or 'TPEx'
    industry = Column(String(50), nullable=True)
    listed_date = Column(Date, nullable=True)
    # Latest valuation from TWSE PER/PBR API
    per = Column(DECIMAL(10, 2), nullable=True)
    pbr = Column(DECIMAL(10, 2), nullable=True)
    dividend_yield = Column(DECIMAL(8, 2), nullable=True)

    def __repr__(self) -> str:
        return f"<Stock {self.stock_id}: {self.stock_name}>"
