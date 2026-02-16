"""Institutional investor trading model."""
from sqlalchemy import Column, Integer, String, Date, BigInteger, UniqueConstraint, Index
from app.database import Base
from app.models.base import TimestampMixin


class Institutional(Base, TimestampMixin):
    """Institutional investor trading data (foreign, trust, dealer)."""

    __tablename__ = "institutionals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(String(10), nullable=False, index=True)
    trade_date = Column(Date, nullable=False)
    foreign_buy = Column(BigInteger, nullable=False, default=0)
    foreign_sell = Column(BigInteger, nullable=False, default=0)
    foreign_net = Column(BigInteger, nullable=False, default=0)
    trust_buy = Column(BigInteger, nullable=False, default=0)
    trust_sell = Column(BigInteger, nullable=False, default=0)
    trust_net = Column(BigInteger, nullable=False, default=0)
    dealer_buy = Column(BigInteger, nullable=False, default=0)
    dealer_sell = Column(BigInteger, nullable=False, default=0)
    dealer_net = Column(BigInteger, nullable=False, default=0)
    total_net = Column(BigInteger, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint('stock_id', 'trade_date', name='uix_institutional_stock_date'),
        Index('ix_institutional_stock_date', 'stock_id', 'trade_date'),
    )

    def __repr__(self) -> str:
        return f"<Institutional {self.stock_id} {self.trade_date}>"
