"""Margin trading and short selling model."""
from sqlalchemy import Column, Integer, String, Date, BigInteger, UniqueConstraint, Index
from app.database import Base
from app.models.base import TimestampMixin


class MarginTrading(Base, TimestampMixin):
    """Margin trading and short selling data."""

    __tablename__ = "margin_tradings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(String(10), nullable=False, index=True)
    trade_date = Column(Date, nullable=False)
    margin_buy = Column(BigInteger, nullable=False, default=0)
    margin_sell = Column(BigInteger, nullable=False, default=0)
    margin_balance = Column(BigInteger, nullable=False, default=0)
    margin_change = Column(BigInteger, nullable=False, default=0)
    short_buy = Column(BigInteger, nullable=False, default=0)
    short_sell = Column(BigInteger, nullable=False, default=0)
    short_balance = Column(BigInteger, nullable=False, default=0)
    short_change = Column(BigInteger, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint('stock_id', 'trade_date', name='uix_margin_stock_date'),
        Index('ix_margin_stock_date', 'stock_id', 'trade_date'),
    )

    def __repr__(self) -> str:
        return f"<MarginTrading {self.stock_id} {self.trade_date}>"
