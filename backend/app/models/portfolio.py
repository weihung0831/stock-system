"""Portfolio model for tracking user holdings."""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint
from app.database import Base
from app.models.base import TimestampMixin


class Portfolio(Base, TimestampMixin):
    """User's stock holding for real-time monitoring."""

    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    stock_id = Column(String(10), nullable=False)
    stock_name = Column(String(50), nullable=False)
    cost_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    target_return_pct = Column(Float, nullable=False)
    entry_momentum_grade = Column(String(10), nullable=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'stock_id', name='uix_portfolio_user_stock'),
    )

    def __repr__(self) -> str:
        return f"<Portfolio {self.stock_id} user={self.user_id} qty={self.quantity}>"
