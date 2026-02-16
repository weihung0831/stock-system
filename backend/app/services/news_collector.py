"""News collector service using Google News RSS feed."""
import logging
from typing import List, Dict
from datetime import datetime
import feedparser

logger = logging.getLogger(__name__)


class NewsCollector:
    """Collector for news articles using Google News RSS."""

    BASE_URL = "https://news.google.com/rss/search"

    def fetch_news(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Fetch news articles from Google News RSS.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of news article dictionaries
        """
        try:
            # Build RSS URL with query
            url = f"{self.BASE_URL}?q={query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"

            # Parse RSS feed
            feed = feedparser.parse(url)

            if not feed.entries:
                logger.warning(f"No news found for query: {query}")
                return []

            # Extract article information
            articles = []
            for entry in feed.entries[:max_results]:
                article = {
                    'title': entry.get('title', ''),
                    'source': entry.get('source', {}).get('title', 'Google News'),
                    'url': entry.get('link', ''),
                    'published_at': self._parse_published_date(entry),
                    'content': entry.get('summary', '')
                }
                articles.append(article)

            logger.info(f"Fetched {len(articles)} news articles for query: {query}")
            return articles

        except Exception as e:
            logger.error(f"Failed to fetch news for query '{query}': {e}")
            return []

    def _parse_published_date(self, entry: Dict) -> str:
        """
        Parse published date from RSS entry.

        Args:
            entry: RSS feed entry

        Returns:
            ISO format datetime string
        """
        try:
            if 'published_parsed' in entry and entry.published_parsed:
                dt = datetime(*entry.published_parsed[:6])
                return dt.isoformat()
            else:
                # Fallback to current time if not available
                return datetime.utcnow().isoformat()
        except Exception as e:
            logger.warning(f"Failed to parse published date: {e}")
            return datetime.utcnow().isoformat()
