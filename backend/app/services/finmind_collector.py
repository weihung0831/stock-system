"""FinMind data collector service using direct HTTP API."""
import logging
import time
from typing import List, Dict, Optional
import pandas as pd
import requests

logger = logging.getLogger(__name__)

FINMIND_API = "https://api.finmindtrade.com/api/v4/data"


class FinMindCollector:
    """Collector for Taiwan stock data using FinMind v4 API directly."""

    def __init__(self, token: str):
        self.token = token

    def _get(self, dataset: str, data_id: str = "", start_date: str = "", end_date: str = "") -> Optional[pd.DataFrame]:
        """Make GET request to FinMind v4 API."""
        params = {
            "dataset": dataset,
            "data_id": data_id,
            "start_date": start_date,
            "end_date": end_date,
            "token": self.token,
        }
        # Remove empty params
        params = {k: v for k, v in params.items() if v}

        for attempt in range(3):
            try:
                resp = requests.get(FINMIND_API, params=params, timeout=120)
                if resp.status_code == 200:
                    body = resp.json()
                    if body.get("msg") == "success" and body.get("data"):
                        return pd.DataFrame(body["data"])
                    logger.warning(f"FinMind empty response for {dataset}/{data_id}: {body.get('msg')}")
                    return pd.DataFrame()
                elif resp.status_code == 429:
                    logger.warning(f"Rate limited, waiting 60s (attempt {attempt+1})")
                    time.sleep(60)
                    continue
                else:
                    logger.error(f"FinMind API error {resp.status_code}: {resp.text[:200]}")
                    return None
            except requests.Timeout:
                logger.warning(f"Timeout for {dataset}/{data_id}, retrying...")
                continue
            except Exception as e:
                logger.error(f"FinMind request error: {e}")
                return None
        return None

    def fetch_stock_list(self) -> List[Dict[str, str]]:
        """Fetch list of all Taiwan stocks."""
        df = self._get("TaiwanStockInfo")
        if df is None or df.empty:
            return []
        cols = ['stock_id', 'stock_name']
        if 'type' in df.columns:
            cols.append('type')
        if 'industry_category' in df.columns:
            cols.append('industry_category')
        stocks = df[cols].to_dict('records')
        logger.info(f"Fetched {len(stocks)} stocks")
        return stocks

    def fetch_all_daily_prices(self, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Bulk fetch daily prices for ALL stocks (single API call)."""
        logger.info(f"Bulk fetching daily prices {start_date} to {end_date}")
        return self._get("TaiwanStockPrice", start_date=start_date, end_date=end_date)

    def fetch_all_institutional(self, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Bulk fetch institutional data for ALL stocks."""
        logger.info(f"Bulk fetching institutional data {start_date} to {end_date}")
        return self._get("TaiwanStockInstitutionalInvestorsBuySell", start_date=start_date, end_date=end_date)

    def fetch_all_margin(self, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Bulk fetch margin trading data for ALL stocks."""
        logger.info(f"Bulk fetching margin data {start_date} to {end_date}")
        return self._get("TaiwanStockMarginPurchaseShortSale", start_date=start_date, end_date=end_date)

    def fetch_daily_prices(self, stock_id: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Fetch daily price data for a single stock."""
        return self._get("TaiwanStockPrice", data_id=stock_id, start_date=start_date, end_date=end_date)

    def fetch_institutional(self, stock_id: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Fetch institutional investor data for a single stock."""
        return self._get("TaiwanStockInstitutionalInvestorsBuySell", data_id=stock_id, start_date=start_date, end_date=end_date)

    def fetch_margin_trading(self, stock_id: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Fetch margin trading data for a single stock."""
        return self._get("TaiwanStockMarginPurchaseShortSale", data_id=stock_id, start_date=start_date, end_date=end_date)

    def fetch_revenue(self, stock_id: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Fetch monthly revenue data."""
        return self._get("TaiwanStockMonthRevenue", data_id=stock_id, start_date=start_date, end_date=end_date)

    def fetch_financial(self, stock_id: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Fetch quarterly financial statement data."""
        return self._get("TaiwanStockFinancialStatements", data_id=stock_id, start_date=start_date, end_date=end_date)
