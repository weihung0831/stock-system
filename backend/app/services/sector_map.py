"""兩層族群分類模組：TWSE 產業 + 自定義族群覆蓋。"""
import json
import logging
import math
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy.orm import Session

from app.models.stock import Stock

logger = logging.getLogger(__name__)

CUSTOM_SECTORS_PATH = Path(__file__).resolve().parents[2] / "config" / "custom_sectors.json"
DEFAULT_SECTOR = "其他"


def _load_custom_sectors(path: Path) -> dict[str, str]:
    """讀取自定義族群 JSON，回傳 {stock_id: sector_name}。"""
    if not path.exists():
        return {}
    try:
        data: dict[str, list[str]] = json.loads(path.read_text(encoding="utf-8"))
        mapping: dict[str, str] = {}
        for sector_name, stock_ids in data.items():
            for sid in stock_ids:
                mapping[sid] = sector_name
        return mapping
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("自定義族群 JSON 解析失敗: %s", exc)
        return {}


def load_sector_map(
    db: Session,
    custom_path: Optional[Path] = None,
) -> dict[str, str]:
    """
    建立 stock_id -> sector_name 映射。

    Layer 1: 從 Stock.industry 讀取 TWSE 產業分類。
    Layer 2: 讀取 custom_sectors.json，覆蓋 Layer 1。
    """
    # Layer 1: TWSE 產業
    rows = db.query(Stock.stock_id, Stock.industry).all()
    sector_map: dict[str, str] = {
        row.stock_id: (row.industry or DEFAULT_SECTOR) for row in rows
    }

    # Layer 2: 自定義覆蓋
    custom = _load_custom_sectors(custom_path or CUSTOM_SECTORS_PATH)
    sector_map.update(custom)

    return sector_map


def rank_sectors(
    sector_map: dict[str, str],
    price_data: dict[str, pd.DataFrame],
    n: int = 5,
) -> list[tuple[str, float]]:
    """
    計算每族群成分股 20 日平均報酬，回傳前 n 名。

    Args:
        sector_map: {stock_id: sector_name}
        price_data: {stock_id: DataFrame with 'close' 欄位}
        n: 回傳數量
    """
    sector_returns: dict[str, list[float]] = {}

    for stock_id, sector in sector_map.items():
        df = price_data.get(stock_id)
        if df is None or df.empty:
            continue
        close_col = "close" if "close" in df.columns else "Close" if "Close" in df.columns else None
        if close_col is None:
            continue
        if len(df) < 21:
            continue
        close = df[close_col].dropna().iloc[-21:]
        if len(close) < 2 or close.iloc[0] == 0:
            continue
        ret = (close.iloc[-1] - close.iloc[0]) / close.iloc[0]
        if math.isnan(ret) or math.isinf(ret):
            continue
        sector_returns.setdefault(sector, []).append(ret)

    # 每族群取平均，排除空族群
    sector_avg = [
        (sector, sum(rets) / len(rets))
        for sector, rets in sector_returns.items()
        if rets
    ]
    sector_avg.sort(key=lambda x: x[1], reverse=True)
    return sector_avg[:n]


def get_stock_sector(stock_id: str, sector_map: dict[str, str]) -> str:
    """回傳該股票的族群名稱，找不到時回傳 '其他'。"""
    return sector_map.get(stock_id, DEFAULT_SECTOR)
