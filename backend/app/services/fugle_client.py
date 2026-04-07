"""Fugle MarketData REST client for real-time stock quotes."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass

from app.config import settings

logger = logging.getLogger(__name__)

TZ_TAIPEI = timezone(timedelta(hours=8))


@dataclass
class QuoteData:
    """Real-time quote data for a stock."""
    price: float
    change: float
    change_pct: float
    name: str


def is_market_open() -> bool:
    """Check if Taiwan stock market is currently open (9:00-13:30, Mon-Fri)."""
    now = datetime.now(TZ_TAIPEI)
    if now.weekday() >= 5:
        return False
    market_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
    market_close = now.replace(hour=13, minute=30, second=0, microsecond=0)
    return market_open <= now <= market_close


def is_quote_available() -> bool:
    """Check if Fugle API can return today's price (market hours + 1hr buffer)."""
    now = datetime.now(TZ_TAIPEI)
    if now.weekday() >= 5:
        return False
    market_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
    buffer_close = now.replace(hour=14, minute=30, second=0, microsecond=0)
    return market_open <= now <= buffer_close


_client_instance = None


def _get_client():
    """Get or create singleton Fugle RestClient."""
    global _client_instance
    if _client_instance is not None:
        return _client_instance
    try:
        from fugle_marketdata import RestClient
        _client_instance = RestClient(api_key=settings.FUGLE_API_KEY)
        return _client_instance
    except Exception as e:
        logger.error(f"Failed to create Fugle client: {e}")
        return None


def get_quotes(stock_ids: List[str]) -> Dict[str, Optional[QuoteData]]:
    """
    Fetch real-time quotes for multiple stocks from Fugle API.

    Returns dict mapping stock_id to QuoteData, or None if fetch failed.
    """
    if not stock_ids:
        return {}

    if not settings or not settings.FUGLE_API_KEY:
        logger.warning("FUGLE_API_KEY not configured")
        return {sid: None for sid in stock_ids}

    client = _get_client()
    if client is None:
        return {sid: None for sid in stock_ids}

    results: Dict[str, Optional[QuoteData]] = {}
    for stock_id in stock_ids:
        try:
            data = client.stock.intraday.quote(symbol=stock_id)
            price = data.get("closePrice") or data.get("lastPrice")
            if price is None:
                results[stock_id] = None
                continue
            results[stock_id] = QuoteData(
                price=float(price),
                change=float(data.get("change", 0)),
                change_pct=float(data.get("changePercent", 0)),
                name=data.get("name", ""),
            )
        except Exception as e:
            logger.warning(f"Failed to fetch quote for {stock_id}: {e}")
            results[stock_id] = None

    return results
