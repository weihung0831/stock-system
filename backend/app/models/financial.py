"""Quarterly financial statement model."""
from sqlalchemy import Column, Integer, String, Date, BigInteger, DECIMAL, UniqueConstraint, Index
from app.database import Base
from app.models.base import TimestampMixin


class Financial(Base, TimestampMixin):
    """Quarterly financial statement data."""

    __tablename__ = "financials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(String(10), nullable=False, index=True)
    report_date = Column(Date, nullable=False)  # Quarter end date
    eps = Column(DECIMAL(10, 4), nullable=False)
    gross_margin = Column(DECIMAL(8, 4), nullable=True)
    operating_margin = Column(DECIMAL(8, 4), nullable=True)
    roe = Column(DECIMAL(8, 4), nullable=True)  # Return on Equity
    debt_ratio = Column(DECIMAL(8, 4), nullable=True)
    operating_cash_flow = Column(BigInteger, nullable=True)
    free_cash_flow = Column(BigInteger, nullable=True)

    __table_args__ = (
        UniqueConstraint('stock_id', 'report_date', name='uix_financial_stock_date'),
        Index('ix_financial_stock_date', 'stock_id', 'report_date'),
    )

    def __repr__(self) -> str:
        return f"<Financial {self.stock_id} {self.report_date}>"
