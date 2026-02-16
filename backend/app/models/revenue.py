"""Monthly revenue model."""
from sqlalchemy import Column, Integer, String, Date, BigInteger, DECIMAL, UniqueConstraint, Index
from app.database import Base
from app.models.base import TimestampMixin


class Revenue(Base, TimestampMixin):
    """Monthly revenue data."""

    __tablename__ = "revenues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(String(10), nullable=False, index=True)
    revenue_date = Column(Date, nullable=False)  # First day of month
    revenue = Column(BigInteger, nullable=False)
    revenue_yoy = Column(DECIMAL(10, 4), nullable=False)  # Year-over-year percentage
    revenue_mom = Column(DECIMAL(10, 4), nullable=True)  # Month-over-month percentage

    __table_args__ = (
        UniqueConstraint('stock_id', 'revenue_date', name='uix_revenue_stock_date'),
        Index('ix_revenue_stock_date', 'stock_id', 'revenue_date'),
    )

    def __repr__(self) -> str:
        return f"<Revenue {self.stock_id} {self.revenue_date}>"
