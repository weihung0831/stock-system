"""動能策略協調器 — 串接完整動能策略管線。"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

import pandas as pd
from sqlalchemy.orm import Session

from app.models.daily_price import DailyPrice
from app.models.market_index import MarketIndex
from app.models.score_result import ScoreResult
from app.services.momentum.filters import run_all_filters
from app.services.momentum.signals import (
    detect_accumulation,
    detect_breakout,
    detect_momentum_stock,
)
from app.services.momentum_scoring import (
    calculate_momentum_score,
    calculate_trading_plan,
    classify,
)
from app.services.sector_map import load_sector_map, rank_sectors, get_stock_sector
from app.services.technical_indicators import (
    calculate_adx,
    calculate_return,
    calculate_rs,
    calculate_rsi,
)

logger = logging.getLogger(__name__)

MARKET_LOOKBACK_DAYS = 120
STOCK_LOOKBACK_DAYS = 120
TOP_SECTOR_COUNT = 5


class MomentumStrategy:
    """動能策略協調器。"""

    def __init__(self, db_session: Session):
        self.db = db_session

    def run(self, as_of_date: Optional[date] = None) -> dict:
        """主要進入點。執行完整的動能策略管線。"""
        if as_of_date:
            ref_date = as_of_date
        else:
            # 用最後一個有大盤資料的交易日
            from sqlalchemy import func as sqlfunc
            latest_market = self.db.query(sqlfunc.max(MarketIndex.date)).scalar()
            ref_date = latest_market if latest_market else date.today()
        logger.info("動能策略啟動，基準日期: %s", ref_date)

        # 1. 載入 TAIEX 資料
        market_df = self._load_market_data(ref_date)
        if market_df.empty or len(market_df) < 60:
            logger.warning("大盤資料不足，無法判斷趨勢")
            return {"market_status": "NO_DATA", "results": []}

        # 2. 判斷市場趨勢
        market_status = self._check_market_trend(market_df)

        # 3. DOWNTREND → 儲存空記錄後回傳
        if market_status == "DOWNTREND":
            self._save_downtrend_record(ref_date)
            return {"market_status": "DOWNTREND", "results": []}

        # 4-5. 族群映射與排名
        sector_map = load_sector_map(self.db)
        stocks_data = self._load_all_stock_data(ref_date)

        # 多取一些族群供前端顯示（前端會選前 5 個有股票的）
        all_ranked_sectors = rank_sectors(sector_map, stocks_data, 15)
        top_sectors = all_ranked_sectors[:TOP_SECTOR_COUNT]
        top_sector_names = {s[0] for s in top_sectors}

        # 6-7. 篩選管線
        filtered = run_all_filters(stocks_data, market_df)
        logger.info("篩選後剩餘 %d 檔股票", len(filtered))

        if not filtered:
            self._clear_and_save(ref_date, [])
            return {
                "market_status": "UPTREND",
                "top_sectors": top_sectors,
                "results": [],
            }

        # 8. 逐股計算信號、指標、評分
        market_return = calculate_return(market_df["Close"], 20)
        results: List[dict] = []

        for stock_id, df in filtered.items():
            try:
                row = self._evaluate_stock(
                    stock_id, df, market_df, market_return,
                    sector_map, top_sector_names,
                )
                if row:
                    results.append(row)
            except Exception:
                logger.exception("評估 %s 發生錯誤", stock_id)

        # 9. 排序與分配 rank
        results.sort(key=lambda r: r["momentum_score"], reverse=True)
        for i, r in enumerate(results, 1):
            r["rank"] = i

        # 10. 批次寫入 DB
        self._clear_and_save(ref_date, results)

        # 11. 儲存 top_sectors 到 SystemSetting 供 API 讀取
        self._save_top_sectors(all_ranked_sectors)

        logger.info("動能策略完成，共 %d 檔上榜", len(results))
        return {
            "market_status": "UPTREND",
            "top_sectors": top_sectors,
            "results": results,
        }

    # ── 私有方法 ──────────────────────────────────────────

    def _load_market_data(self, ref_date: date) -> pd.DataFrame:
        cutoff = ref_date - timedelta(days=MARKET_LOOKBACK_DAYS * 2)
        rows = (
            self.db.query(MarketIndex)
            .filter(MarketIndex.date <= ref_date, MarketIndex.date >= cutoff)
            .order_by(MarketIndex.date)
            .all()
        )
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(
            [{"Close": float(r.close), "High": float(r.high),
              "Low": float(r.low), "Volume": r.volume or 0} for r in rows],
            index=pd.Index([r.date for r in rows]),
        )

    def _check_market_trend(self, market_df: pd.DataFrame) -> str:
        closes = market_df["Close"]
        ma20 = closes.rolling(20).mean().iloc[-1]
        ma60 = closes.rolling(60).mean().iloc[-1]
        return "UPTREND" if ma20 >= ma60 else "DOWNTREND"

    def _load_all_stock_data(self, ref_date: date) -> Dict[str, pd.DataFrame]:
        cutoff = ref_date - timedelta(days=STOCK_LOOKBACK_DAYS * 2)
        rows = (
            self.db.query(DailyPrice)
            .filter(DailyPrice.trade_date <= ref_date, DailyPrice.trade_date >= cutoff)
            .order_by(DailyPrice.stock_id, DailyPrice.trade_date)
            .all()
        )
        grouped: Dict[str, list] = {}
        for r in rows:
            grouped.setdefault(r.stock_id, []).append(r)

        result: Dict[str, pd.DataFrame] = {}
        for stock_id, records in grouped.items():
            result[stock_id] = pd.DataFrame(
                [{"Close": float(r.close), "High": float(r.high),
                  "Low": float(r.low), "Open": float(r.open),
                  "Volume": int(r.volume)} for r in records],
                index=pd.Index([r.trade_date for r in records]),
            )
        return result

    def _evaluate_stock(
        self, stock_id: str, df: pd.DataFrame,
        market_df: pd.DataFrame, market_return: float,
        sector_map: dict, top_sector_names: set,
    ) -> Optional[dict]:
        acc_passed, acc_score = detect_accumulation(df)
        brk_passed, brk_mag = detect_breakout(df)
        is_momentum = detect_momentum_stock(df, market_df)

        rsi = calculate_rsi(df["Close"], 14)
        adx = calculate_adx(df["High"], df["Low"], df["Close"], 14)
        stock_return = calculate_return(df["Close"], 20)
        rs = calculate_rs(stock_return, market_return)
        vol_ratio = (
            df["Volume"].iloc[-5:].mean() / df["Volume"].iloc[-20:].mean()
            if df["Volume"].iloc[-20:].mean() > 0 else 0
        )

        m_score = calculate_momentum_score(
            rs=rs,
            rsi=float(rsi.iloc[-1]) if pd.notna(rsi.iloc[-1]) else 50,
            adx=float(adx.iloc[-1]) if pd.notna(adx.iloc[-1]) else 0,
            volume_ratio=vol_ratio,
            breakout_magnitude=brk_mag,
            accumulation_score=acc_score,
        )

        sector_name = get_stock_sector(stock_id, sector_map)
        in_top = sector_name in top_sector_names
        cls = classify(m_score, brk_passed, acc_passed, in_top)
        plan = calculate_trading_plan(df)

        return {
            "stock_id": stock_id,
            "momentum_score": round(m_score, 2),
            "classification": cls,
            "sector_name": sector_name,
            "is_momentum_stock": is_momentum,
            **plan,
        }

    def _save_downtrend_record(self, ref_date: date) -> None:
        self.db.query(ScoreResult).filter(
            ScoreResult.score_date == ref_date
        ).delete()
        record = ScoreResult(
            stock_id="MARKET",
            score_date=ref_date,
            total_score=Decimal("0"),
            rank=0,
            market_status="DOWNTREND",
        )
        self.db.add(record)
        self.db.commit()

    def _clear_and_save(self, ref_date: date, results: List[dict]) -> None:
        self.db.query(ScoreResult).filter(
            ScoreResult.score_date == ref_date
        ).delete()
        for r in results:
            record = ScoreResult(
                stock_id=r["stock_id"],
                score_date=ref_date,
                total_score=Decimal(str(r["momentum_score"])),
                momentum_score=Decimal(str(r["momentum_score"])),
                rank=r["rank"],
                classification=r["classification"],
                sector_name=r.get("sector_name"),
                buy_price=Decimal(str(r["buy_price"])) if r.get("buy_price") else None,
                stop_price=Decimal(str(r["stop_price"])) if r.get("stop_price") else None,
                add_price=Decimal(str(r["add_price"])) if r.get("add_price") else None,
                target_price=Decimal(str(r["target_price"])) if r.get("target_price") else None,
                market_status="UPTREND",
            )
            self.db.add(record)
        self.db.commit()

    def _save_top_sectors(self, top_sectors: list) -> None:
        """將族群排名儲存到 JSON 檔案供 API 讀取。"""
        import json
        import os

        import math
        data = []
        for s in top_sectors:
            val = float(s[1]) * 100
            if math.isnan(val) or math.isinf(val):
                val = 0.0
            data.append({"name": s[0], "return_pct": round(val, 2)})
        path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "top_sectors_cache.json")
        path = os.path.normpath(path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
