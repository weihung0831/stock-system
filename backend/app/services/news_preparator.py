"""News data preparation service for LLM input."""
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.news import News
from app.models.stock import Stock
from app.services.news_collector import NewsCollector

logger = logging.getLogger(__name__)


class NewsPreparator:
    """Prepare news data for LLM analysis, fetching on-demand if needed."""

    def __init__(self):
        self.collector = NewsCollector()

    def prepare_stock_news(self, db: Session, stock_id: str, days: int = 14) -> str:
        """
        Get recent news for a stock and format for LLM input.
        If no news in DB, fetch from Google News RSS on-demand.

        Args:
            db: Database session
            stock_id: Stock ticker (e.g., "2330")
            days: Number of days to look back

        Returns:
            Formatted news string or "近期無重大新聞"
        """
        try:
            date_threshold = datetime.now() - timedelta(days=days)

            # Query existing news from DB
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

            # On-demand fetch if no news found in DB
            if not news_items:
                news_items = self._fetch_and_save(db, stock_id, date_threshold)

            if not news_items:
                return "近期無重大新聞"

            return self._format_news(news_items)

        except Exception as e:
            logger.error(f"Failed to prepare news for {stock_id}: {e}")
            return "近期無重大新聞"

    def _fetch_and_save(self, db: Session, stock_id: str, date_threshold: datetime):
        """Fetch news from Google News RSS and save to DB."""
        stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
        stock_name = stock.stock_name if stock else stock_id
        query = f"{stock_id} {stock_name} 股票"

        articles = self.collector.fetch_news(query=query, max_results=5)
        if not articles:
            return []

        saved_items = []
        for article in articles:
            try:
                published_at = datetime.fromisoformat(article['published_at'])
                # Skip articles older than threshold
                if published_at < date_threshold:
                    continue

                existing = db.query(News).filter_by(url=article['url']).first()
                if not existing:
                    news = News(
                        stock_id=stock_id,
                        title=article['title'],
                        source=article['source'],
                        url=article['url'],
                        published_at=published_at,
                        content=article['content'],
                    )
                    db.add(news)
                    saved_items.append(news)
                else:
                    saved_items.append(existing)
            except Exception as e:
                logger.warning(f"Failed to save article for {stock_id}: {e}")

        if saved_items:
            db.commit()
            logger.info(f"On-demand fetched {len(saved_items)} news for {stock_id}")

        return saved_items

    @staticmethod
    def _format_news(news_items) -> str:
        """Format news items into a concise string for LLM prompt."""
        formatted_items = []
        total_length = 0
        max_length = 500

        for idx, news in enumerate(news_items, 1):
            date_str = news.published_at.strftime("%Y-%m-%d")
            title = news.title[:100]
            news_line = f"{idx}. [{date_str}] {title}"

            if total_length + len(news_line) > max_length:
                break

            formatted_items.append(news_line)
            total_length += len(news_line)

        return "\n".join(formatted_items) if formatted_items else "近期無重大新聞"
