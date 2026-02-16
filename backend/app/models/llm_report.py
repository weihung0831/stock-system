"""LLM-generated stock analysis report model."""
from sqlalchemy import Column, Integer, String, Date, Text, JSON, UniqueConstraint, Index
from app.database import Base
from app.models.base import TimestampMixin


class LLMReport(Base, TimestampMixin):
    """LLM-generated comprehensive stock analysis report."""

    __tablename__ = "llm_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(String(10), nullable=False, index=True)
    report_date = Column(Date, nullable=False)
    chip_analysis = Column(Text, nullable=False)
    fundamental_analysis = Column(Text, nullable=False)
    technical_analysis = Column(Text, nullable=False)
    news_sentiment = Column(String(20), nullable=False)  # positive/neutral/negative
    news_summary = Column(Text, nullable=False)
    risk_alerts = Column(JSON, nullable=False)  # List of risk items
    recommendation = Column(Text, nullable=False)
    confidence = Column(String(10), nullable=False)  # high/medium/low
    raw_response = Column(Text, nullable=True)
    model_used = Column(String(50), nullable=False)

    __table_args__ = (
        UniqueConstraint('stock_id', 'report_date', name='uix_report_stock_date'),
        Index('ix_report_stock_date', 'stock_id', 'report_date'),
    )

    def __repr__(self) -> str:
        return f"<LLMReport {self.stock_id} {self.report_date}>"
