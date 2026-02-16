"""News data preparation service for LLM input."""
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.news import News

logger = logging.getLogger(__name__)


class NewsPreparator:
    """Prepare news data for LLM analysis."""

    def prepare_stock_news(self, db: Session, stock_id: str, days: int = 7) -> str:
        """
        Get recent news for a stock and format for LLM input.

        Args:
            db: Database session
            stock_id: Stock ticker (e.g., "2330")
            days: Number of days to look back

        Returns:
            Formatted news string or "近期無重大新聞"
        """
        try:
            # Calculate date threshold
            date_threshold = datetime.now() - timedelta(days=days)

            # Query news for this stock in the last N days
            news_items = (
                db.query(News)
                .filter(
                    News.stock_id == stock_id,
                    News.published_at >= date_threshold
                )
                .order_by(News.published_at.desc())
                .limit(5)
                .all()
            )

            if not news_items:
                return "近期無重大新聞"

            # Format news items
            formatted_items = []
            total_length = 0
            max_length = 500  # Character limit

            for idx, news in enumerate(news_items, 1):
                # Format date
                date_str = news.published_at.strftime("%Y-%m-%d")

                # Build news line
                title = news.title[:100]  # Truncate long titles
                summary = news.content[:80] if news.content else ""

                if summary:
                    news_line = f"{idx}. [{date_str}] {title} - {summary}"
                else:
                    news_line = f"{idx}. [{date_str}] {title}"

                # Check length limit
                if total_length + len(news_line) > max_length:
                    break

                formatted_items.append(news_line)
                total_length += len(news_line)

            if not formatted_items:
                return "近期無重大新聞"

            return "\n".join(formatted_items)

        except Exception as e:
            logger.error(f"Failed to prepare news for {stock_id}: {e}")
            return "近期無重大新聞"
