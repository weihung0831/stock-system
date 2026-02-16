"""Daily price model for stock trading data."""
from sqlalchemy import Column, Integer, String, Date, DECIMAL, BigInteger, Index, UniqueConstraint
from app.database import Base
from app.models.base import TimestampMixin


class DailyPrice(Base, TimestampMixin):
    """Daily stock price and trading data."""

    __tablename__ = "daily_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(String(10), nullable=False, index=True)
    trade_date = Column(Date, nullable=False)
    open = Column(DECIMAL(19, 4), nullable=False)
    high = Column(DECIMAL(19, 4), nullable=False)
    low = Column(DECIMAL(19, 4), nullable=False)
    close = Column(DECIMAL(19, 4), nullable=False)
    volume = Column(BigInteger, nullable=False)
    turnover = Column(BigInteger, nullable=True)
    change_price = Column(DECIMAL(19, 4), nullable=True)
    change_percent = Column(DECIMAL(8, 4), nullable=True)

    __table_args__ = (
        UniqueConstraint('stock_id', 'trade_date', name='uix_stock_trade_date'),
        Index('ix_daily_price_stock_date', 'stock_id', 'trade_date'),
    )

    def __repr__(self) -> str:
        return f"<DailyPrice {self.stock_id} {self.trade_date}>"
