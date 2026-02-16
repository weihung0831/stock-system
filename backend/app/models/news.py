"""News article model."""
from sqlalchemy import Column, Integer, String, DateTime, Text, Index
from app.database import Base
from app.models.base import TimestampMixin


class News(Base, TimestampMixin):
    """News articles related to stocks."""

    __tablename__ = "news"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(String(10), nullable=True, index=True)  # Nullable for general news
    title = Column(String(500), nullable=False)
    source = Column(String(100), nullable=False)
    url = Column(String(1000), nullable=False)
    published_at = Column(DateTime, nullable=False)
    content = Column(Text, nullable=True)
    sentiment = Column(String(20), nullable=True)  # positive/neutral/negative

    __table_args__ = (
        Index('ix_news_stock_published', 'stock_id', 'published_at'),
    )

    def __repr__(self) -> str:
        return f"<News {self.id}: {self.title[:50]}>"
