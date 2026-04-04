"""Notification model for user alerts."""
from sqlalchemy import Column, Integer, String, Text, Boolean, Date, ForeignKey, UniqueConstraint
from app.database import Base
from app.models.base import TimestampMixin


class Notification(Base, TimestampMixin):
    """User notification for portfolio alerts."""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True)
    type = Column(String(30), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    created_date = Column(Date, nullable=False)

    __table_args__ = (
        UniqueConstraint('portfolio_id', 'type', 'created_date',
                         name='uix_notification_dedup'),
    )

    def __repr__(self) -> str:
        return f"<Notification {self.type} user={self.user_id} read={self.is_read}>"
