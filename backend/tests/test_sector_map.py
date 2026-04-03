"""族群分類模組測試。"""
import json
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from app.services.sector_map import (
    load_sector_map,
    rank_sectors,
    get_stock_sector,
)


class _FakeRow:
    def __init__(self, stock_id: str, industry):
        self.stock_id = stock_id
        self.industry = industry


@pytest.fixture()
def mock_db():
    db = MagicMock()
    db.query.return_value.all.return_value = [
        _FakeRow("2330", "半導體業"),
        _FakeRow("2317", "其他電子業"),
        _FakeRow("2382", "電腦及週邊設備業"),
        _FakeRow("9999", None),
    ]
    return db


@pytest.fixture()
def custom_json(tmp_path: Path) -> Path:
    p = tmp_path / "custom_sectors.json"
    p.write_text(json.dumps({"AI伺服器": ["2382", "2317"]}), encoding="utf-8")
    return p


# --- load_sector_map ---

def test_load_twse_only(mock_db, tmp_path: Path):
    """TWSE 分類載入，無自定義 JSON。"""
    no_file = tmp_path / "not_exist.json"
    result = load_sector_map(mock_db, custom_path=no_file)
    assert result["2330"] == "半導體業"
    assert result["9999"] == "其他"


def test_load_with_custom_override(mock_db, custom_json: Path):
    """自定義 JSON 覆蓋 TWSE 分類。"""
    result = load_sector_map(mock_db, custom_path=custom_json)
    assert result["2382"] == "AI伺服器"
    assert result["2317"] == "AI伺服器"
    assert result["2330"] == "半導體業"


def test_load_json_not_exist_no_error(mock_db, tmp_path: Path):
    """JSON 不存在時不報錯，僅用 TWSE。"""
    result = load_sector_map(mock_db, custom_path=tmp_path / "missing.json")
    assert len(result) == 4


# --- rank_sectors ---

def _make_price_df(prices: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"close": prices})


def test_rank_sectors_basic():
    sector_map = {"A": "半導體", "B": "半導體", "C": "金融"}
    price_data = {
        "A": _make_price_df([100.0] * 10 + [110.0] * 11),
        "B": _make_price_df([100.0] * 10 + [120.0] * 11),
        "C": _make_price_df([100.0] * 10 + [105.0] * 11),
    }
    result = rank_sectors(sector_map, price_data, n=5)
    assert len(result) == 2
    assert result[0][0] == "半導體"
    assert result[0][1] > result[1][1]


def test_rank_sectors_skip_short_data():
    sector_map = {"A": "X"}
    price_data = {"A": _make_price_df([100.0] * 10)}
    result = rank_sectors(sector_map, price_data)
    assert result == []


def test_rank_sectors_skip_empty():
    result = rank_sectors({"A": "X"}, {})
    assert result == []


# --- get_stock_sector ---

def test_get_stock_sector_found():
    assert get_stock_sector("2330", {"2330": "半導體業"}) == "半導體業"


def test_get_stock_sector_not_found():
    assert get_stock_sector("0000", {}) == "其他"
