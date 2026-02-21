"""Track per-user daily AI report generation usage."""
from sqlalchemy import Column, Integer, String, Date, UniqueConstraint, Index
from app.database import Base


class ReportUsage(Base):
    """Records each user's report generation to survive server restarts."""

    __tablename__ = "report_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    stock_id = Column(String(10), nullable=False)
    usage_date = Column(Date, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'stock_id', 'usage_date', name='uix_report_usage'),
        Index('ix_report_usage_user_date', 'user_id', 'usage_date'),
    )
