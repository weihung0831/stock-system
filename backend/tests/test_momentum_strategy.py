"""MomentumStrategy 單元測試。"""
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.daily_price import DailyPrice
from app.models.market_index import MarketIndex
from app.models.score_result import ScoreResult
from app.services.momentum.strategy import MomentumStrategy


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _make_market_rows(session, days: int, trend: str, ref: date = None):
    """產生 MarketIndex 假資料。trend='up' → MA20 >= MA60。"""
    ref = ref or date(2026, 4, 1)
    base = 17000.0
    for i in range(days):
        d = ref - timedelta(days=days - 1 - i)
        if trend == "up":
            close = base + i * 10  # 穩定上漲
        elif trend == "flat":
            close = base  # 持平
        else:
            close = base - i * 10  # 穩定下跌
        row = MarketIndex(
            date=d,
            open=Decimal(str(close)),
            high=Decimal(str(close + 50)),
            low=Decimal(str(close - 50)),
            close=Decimal(str(close)),
            volume=1000000,
        )
        session.add(row)
    session.commit()


def _make_stock_rows(session, stock_id: str, days: int, ref: date = None):
    """產生 DailyPrice 假資料（穩定上漲）。"""
    ref = ref or date(2026, 4, 1)
    base = 100.0
    for i in range(days):
        d = ref - timedelta(days=days - 1 - i)
        close = base + i * 0.5
        row = DailyPrice(
            stock_id=stock_id,
            trade_date=d,
            open=Decimal(str(close)),
            high=Decimal(str(close + 2)),
            low=Decimal(str(close - 2)),
            close=Decimal(str(close)),
            volume=5000,
        )
        session.add(row)
    session.commit()


class TestMomentumStrategyDowntrend:
    def test_downtrend_returns_empty(self, db_session):
        _make_market_rows(db_session, 80, "down")
        strategy = MomentumStrategy(db_session)
        result = strategy.run(as_of_date=date(2026, 4, 1))

        assert result["market_status"] == "DOWNTREND"
        assert result["results"] == []

        # 確認 DB 有 DOWNTREND 記錄
        record = db_session.query(ScoreResult).first()
        assert record is not None
        assert record.stock_id == "MARKET"
        assert record.market_status == "DOWNTREND"

    def test_insufficient_market_data(self, db_session):
        _make_market_rows(db_session, 30, "up")
        strategy = MomentumStrategy(db_session)
        result = strategy.run(as_of_date=date(2026, 4, 1))
        assert result["market_status"] == "NO_DATA"


class TestMomentumStrategyUptrend:
    def test_ma20_eq_ma60_is_uptrend(self, db_session):
        """MA20 == MA60（持平）應判定為 UPTREND。"""
        _make_market_rows(db_session, 80, "flat")
        strategy = MomentumStrategy(db_session)
        result = strategy.run(as_of_date=date(2026, 4, 1))
        assert result["market_status"] == "UPTREND"

    @patch("app.services.momentum.strategy.load_sector_map", return_value={})
    @patch("app.services.momentum.strategy.rank_sectors", return_value=[])
    def test_uptrend_with_no_stocks(self, mock_rank, mock_sector, db_session):
        """UPTREND 但無個股資料時回傳空結果。"""
        _make_market_rows(db_session, 80, "up")
        strategy = MomentumStrategy(db_session)
        result = strategy.run(as_of_date=date(2026, 4, 1))

        assert result["market_status"] == "UPTREND"
        assert result["results"] == []

    @patch("app.services.momentum.strategy.load_sector_map", return_value={"2330": "半導體"})
    @patch("app.services.momentum.strategy.rank_sectors", return_value=[("半導體", 0.05)])
    def test_uptrend_full_pipeline(self, mock_rank, mock_sector, db_session):
        """UPTREND 完整管線：有個股通過篩選時應產出結果。"""
        ref = date(2026, 4, 1)
        _make_market_rows(db_session, 100, "up", ref)
        _make_stock_rows(db_session, "2330", 100, ref)

        strategy = MomentumStrategy(db_session)

        # Mock filters 讓股票通過篩選
        with patch("app.services.momentum.strategy.run_all_filters") as mock_f:
            # 建立與 _load_all_stock_data 相同格式的 DataFrame
            rows = db_session.query(DailyPrice).filter(
                DailyPrice.stock_id == "2330"
            ).order_by(DailyPrice.trade_date).all()
            df = pd.DataFrame(
                [{"Close": float(r.close), "High": float(r.high),
                  "Low": float(r.low), "Open": float(r.open),
                  "Volume": int(r.volume)} for r in rows],
                index=pd.Index([r.trade_date for r in rows]),
            )
            mock_f.return_value = {"2330": df}

            result = strategy.run(as_of_date=ref)

        assert result["market_status"] == "UPTREND"
        assert len(result["results"]) == 1
        assert result["results"][0]["stock_id"] == "2330"
        assert result["results"][0]["rank"] == 1
        assert "momentum_score" in result["results"][0]
        assert "classification" in result["results"][0]

        # 確認 DB 寫入
        records = db_session.query(ScoreResult).filter(
            ScoreResult.score_date == ref, ScoreResult.stock_id != "MARKET"
        ).all()
        assert len(records) == 1
        assert records[0].market_status == "UPTREND"
