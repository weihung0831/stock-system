"""Score result model for multi-factor screening."""
from sqlalchemy import Column, Integer, String, Date, DECIMAL, UniqueConstraint, Index
from app.database import Base
from app.models.base import TimestampMixin


class ScoreResult(Base, TimestampMixin):
    """Multi-factor screening score results."""

    __tablename__ = "score_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(String(10), nullable=False, index=True)
    score_date = Column(Date, nullable=False)
    chip_score = Column(DECIMAL(6, 2), nullable=False)
    fundamental_score = Column(DECIMAL(6, 2), nullable=False)
    technical_score = Column(DECIMAL(6, 2), nullable=False)
    total_score = Column(DECIMAL(6, 2), nullable=False)
    rank = Column(Integer, nullable=False)
    chip_weight = Column(DECIMAL(5, 2), nullable=False)
    fundamental_weight = Column(DECIMAL(5, 2), nullable=False)
    technical_weight = Column(DECIMAL(5, 2), nullable=False)

    __table_args__ = (
        UniqueConstraint('stock_id', 'score_date', name='uix_score_stock_date'),
        Index('ix_score_stock_date', 'stock_id', 'score_date'),
    )

    def __repr__(self) -> str:
        return f"<ScoreResult {self.stock_id} {self.score_date} rank={self.rank}>"
