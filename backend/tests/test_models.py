"""Tests for SQLAlchemy ORM models."""
import pytest
from datetime import datetime, date
from decimal import Decimal

from app.models.stock import Stock
from app.models.user import User
from app.models.daily_price import DailyPrice
from app.models.system_setting import SystemSetting
from app.models.score_result import ScoreResult
from app.models.sector_tag import SectorTag
from app.models.base import TimestampMixin


class TestStockModel:
    """Tests for Stock ORM model."""

    def test_stock_creation(self, test_db):
        """Test creating a stock record."""
        stock = Stock(
            stock_id="2330",
            stock_name="台積電",
            market="TWSE",
            industry="半導體",
            listed_date=date(1994, 6, 30)
        )
        test_db.add(stock)
        test_db.commit()

        assert stock.id is not None
        assert stock.stock_id == "2330"
        assert stock.stock_name == "台積電"

    def test_stock_repr(self, test_stock):
        """Test stock string representation."""
        assert repr(test_stock) == "<Stock 2330: 台積電>"

    def test_stock_unique_constraint(self, test_db):
        """Test stock_id unique constraint."""
        stock1 = Stock(
            stock_id="2330",
            stock_name="台積電",
            market="TWSE"
        )
        test_db.add(stock1)
        test_db.commit()

        # Try to add duplicate stock_id
        stock2 = Stock(
            stock_id="2330",
            stock_name="Duplicate",
            market="TWSE"
        )
        test_db.add(stock2)

        with pytest.raises(Exception):  # IntegrityError
            test_db.commit()

    def test_stock_nullable_fields(self, test_db):
        """Test that nullable fields can be None."""
        stock = Stock(
            stock_id="9999",
            stock_name="Test Stock",
            market="TPEx",
            industry=None,
            listed_date=None
        )
        test_db.add(stock)
        test_db.commit()

        assert stock.industry is None
        assert stock.listed_date is None

    def test_stock_timestamps(self, test_db, test_stock):
        """Test timestamp mixin timestamps."""
        assert test_stock.created_at is not None
        assert test_stock.updated_at is not None
        assert isinstance(test_stock.created_at, datetime)
        assert isinstance(test_stock.updated_at, datetime)


class TestUserModel:
    """Tests for User ORM model."""

    def test_user_creation(self, test_db):
        """Test creating a user record."""
        user = User(
            username="newuser",
            email="newuser@test.com",
            hashed_password="hashed_pass_value",
            is_admin=False,
            is_active=True
        )
        test_db.add(user)
        test_db.commit()

        assert user.id is not None
        assert user.username == "newuser"
        assert user.is_active is True

    def test_user_repr(self, test_user):
        """Test user string representation."""
        assert repr(test_user) == "<User testuser tier=free admin=False>"

    def test_user_admin_repr(self, test_admin_user):
        """Test admin user string representation."""
        assert repr(test_admin_user) == "<User adminuser tier=free admin=True>"

    def test_user_unique_username(self, test_db, test_user):
        """Test username unique constraint."""
        duplicate_user = User(
            username="testuser",
            email="dup@test.com",
            hashed_password="different_hash",
            is_admin=False,
            is_active=True
        )
        test_db.add(duplicate_user)

        with pytest.raises(Exception):  # IntegrityError
            test_db.commit()

    def test_user_default_is_admin_false(self, test_db):
        """Test default is_admin is False."""
        user = User(
            username="user1",
            email="user1@test.com",
            hashed_password="pass",
        )
        test_db.add(user)
        test_db.commit()

        assert user.is_admin is False

    def test_user_default_is_active_true(self, test_db):
        """Test default is_active is True."""
        user = User(
            username="user2",
            email="user2@test.com",
            hashed_password="pass",
        )
        test_db.add(user)
        test_db.commit()

        assert user.is_active is True

    def test_user_timestamps(self, test_db, test_user):
        """Test user has timestamp mixin."""
        assert test_user.created_at is not None
        assert test_user.updated_at is not None


class TestDailyPriceModel:
    """Tests for DailyPrice ORM model."""

    def test_daily_price_creation(self, test_db, test_stock):
        """Test creating daily price record."""
        price = DailyPrice(
            stock_id=test_stock.stock_id,
            trade_date=date(2024, 1, 15),
            open=Decimal("600.50"),
            high=Decimal("610.75"),
            low=Decimal("595.25"),
            close=Decimal("605.00"),
            volume=1000000,
            turnover=605000000
        )
        test_db.add(price)
        test_db.commit()

        assert price.id is not None
        assert price.stock_id == test_stock.stock_id
        assert price.close == Decimal("605.00")

    def test_daily_price_repr(self, test_daily_prices):
        """Test daily price string representation."""
        price = test_daily_prices[0]
        assert repr(price) == f"<DailyPrice {price.stock_id} {price.trade_date}>"

    def test_daily_price_unique_constraint(self, test_db, test_stock):
        """Test stock_id + trade_date unique constraint."""
        date1 = date(2024, 1, 15)

        price1 = DailyPrice(
            stock_id=test_stock.stock_id,
            trade_date=date1,
            open=600,
            high=610,
            low=590,
            close=605,
            volume=1000000
        )
        test_db.add(price1)
        test_db.commit()

        # Try to add duplicate
        price2 = DailyPrice(
            stock_id=test_stock.stock_id,
            trade_date=date1,
            open=601,
            high=611,
            low=591,
            close=606,
            volume=1000100
        )
        test_db.add(price2)

        with pytest.raises(Exception):  # IntegrityError
            test_db.commit()

    def test_daily_price_nullable_fields(self, test_db, test_stock):
        """Test nullable fields in daily price."""
        price = DailyPrice(
            stock_id=test_stock.stock_id,
            trade_date=date(2024, 1, 16),
            open=600,
            high=610,
            low=590,
            close=605,
            volume=1000000,
            turnover=None,
            change_price=None,
            change_percent=None
        )
        test_db.add(price)
        test_db.commit()

        assert price.turnover is None
        assert price.change_price is None
        assert price.change_percent is None

    def test_daily_price_decimal_precision(self, test_db, test_stock):
        """Test decimal field precision."""
        price = DailyPrice(
            stock_id=test_stock.stock_id,
            trade_date=date(2024, 1, 17),
            open=Decimal("600.1234"),
            high=Decimal("610.5678"),
            low=Decimal("590.9012"),
            close=Decimal("605.3456"),
            volume=1000000,
            change_percent=Decimal("0.8345")
        )
        test_db.add(price)
        test_db.commit()

        # Verify precision is maintained
        assert str(price.open) == "600.1234"
        assert str(price.change_percent) == "0.8345"

    def test_daily_price_large_volume(self, test_db, test_stock):
        """Test large volume values (BigInteger)."""
        large_volume = 999999999999
        price = DailyPrice(
            stock_id=test_stock.stock_id,
            trade_date=date(2024, 1, 18),
            open=600,
            high=610,
            low=590,
            close=605,
            volume=large_volume
        )
        test_db.add(price)
        test_db.commit()

        assert price.volume == large_volume

    def test_daily_price_timestamps(self, test_db, test_stock):
        """Test daily price has timestamp mixin."""
        price = DailyPrice(
            stock_id=test_stock.stock_id,
            trade_date=date.today(),
            open=600,
            high=610,
            low=590,
            close=605,
            volume=1000000
        )
        test_db.add(price)
        test_db.commit()

        assert price.created_at is not None
        assert price.updated_at is not None


class TestTimestampMixin:
    """Tests for TimestampMixin functionality."""

    def test_timestamp_mixin_auto_set(self, test_db, test_user):
        """Test timestamps are automatically set."""
        assert test_user.created_at is not None
        assert test_user.updated_at is not None

    def test_timestamp_mixin_not_older_than_now(self, test_db, test_user):
        """Test timestamps are not older than current time."""
        now = datetime.now()
        assert test_user.created_at <= now
        assert test_user.updated_at <= now

    def test_timestamp_mixin_created_equals_updated_on_insert(self, test_db):
        """Test created_at equals updated_at on initial insert."""
        user = User(
            username="freshuser",
            email="fresh@test.com",
            hashed_password="pass",
            is_admin=False,
            is_active=True
        )
        test_db.add(user)
        test_db.commit()

        # Note: Due to datetime precision, allow small difference
        time_diff = abs((user.created_at - user.updated_at).total_seconds())
        assert time_diff < 1.0  # Less than 1 second difference


class TestSystemSettingModel:
    """Tests for SystemSetting ORM model."""

    def test_system_setting_creation_defaults(self, test_db):
        """Test creating system setting with default values."""
        setting = SystemSetting(id=1)
        test_db.add(setting)
        test_db.commit()

        assert setting.chip_weight == 40
        assert setting.fundamental_weight == 35
        assert setting.technical_weight == 25
        assert setting.screening_threshold == 2.5

    def test_system_setting_scheduler_defaults(self, test_db):
        """Test scheduler fields default values."""
        setting = SystemSetting(id=1)
        test_db.add(setting)
        test_db.commit()

        assert setting.scheduler_enabled == 1
        assert setting.scheduler_hour == 16
        assert setting.scheduler_minute == 30

    def test_system_setting_custom_scheduler(self, test_db):
        """Test setting custom scheduler values."""
        setting = SystemSetting(
            id=1,
            scheduler_enabled=0,
            scheduler_hour=9,
            scheduler_minute=15
        )
        test_db.add(setting)
        test_db.commit()

        assert setting.scheduler_enabled == 0
        assert setting.scheduler_hour == 9
        assert setting.scheduler_minute == 15

    def test_system_setting_custom_weights(self, test_db):
        """Test setting custom weight values."""
        setting = SystemSetting(
            id=1,
            chip_weight=50,
            fundamental_weight=30,
            technical_weight=20,
            screening_threshold=3.0
        )
        test_db.add(setting)
        test_db.commit()

        assert setting.chip_weight == 50
        assert setting.screening_threshold == 3.0

    def test_system_setting_timestamps(self, test_db):
        """Test SystemSetting has timestamp mixin."""
        setting = SystemSetting(id=1)
        test_db.add(setting)
        test_db.commit()

        assert setting.created_at is not None
        assert setting.updated_at is not None


class TestScoreResultModel:
    """Tests for ScoreResult ORM model."""

    def test_score_result_creation(self, test_db):
        """Test creating a score result record."""
        score = ScoreResult(
            stock_id="2330",
            score_date=date(2026, 2, 15),
            chip_score=Decimal("85.50"),
            fundamental_score=Decimal("72.30"),
            technical_score=Decimal("68.10"),
            total_score=Decimal("76.20"),
            rank=1,
            chip_weight=Decimal("40.00"),
            fundamental_weight=Decimal("35.00"),
            technical_weight=Decimal("25.00")
        )
        test_db.add(score)
        test_db.commit()

        assert score.id is not None
        assert score.stock_id == "2330"
        assert score.total_score == Decimal("76.20")
        assert score.rank == 1

    def test_score_result_repr(self, test_db):
        """Test score result string representation."""
        score = ScoreResult(
            stock_id="2330",
            score_date=date(2026, 2, 15),
            chip_score=85, fundamental_score=72,
            technical_score=68, total_score=76,
            rank=1, chip_weight=40,
            fundamental_weight=35, technical_weight=25
        )
        test_db.add(score)
        test_db.commit()

        assert "2330" in repr(score)
        assert "rank=1" in repr(score)

    def test_score_result_unique_constraint(self, test_db):
        """Test stock_id + score_date unique constraint."""
        kwargs = dict(
            stock_id="2330", score_date=date(2026, 2, 15),
            chip_score=85, fundamental_score=72,
            technical_score=68, total_score=76,
            rank=1, chip_weight=40,
            fundamental_weight=35, technical_weight=25
        )
        test_db.add(ScoreResult(**kwargs))
        test_db.commit()

        test_db.add(ScoreResult(**{**kwargs, "rank": 2}))
        with pytest.raises(Exception):
            test_db.commit()

    def test_score_result_timestamps(self, test_db):
        """Test ScoreResult has timestamp mixin."""
        score = ScoreResult(
            stock_id="2330", score_date=date(2026, 2, 15),
            chip_score=85, fundamental_score=72,
            technical_score=68, total_score=76,
            rank=1, chip_weight=40,
            fundamental_weight=35, technical_weight=25
        )
        test_db.add(score)
        test_db.commit()

        assert score.created_at is not None
        assert score.updated_at is not None


class TestSectorTagModel:
    """Tests for SectorTag ORM model."""

    def test_sector_tag_creation(self, test_db):
        """Test creating a sector tag."""
        tag = SectorTag(name="半導體", color="#3b82f6", keywords="晶片,IC", sort_order=1)
        test_db.add(tag)
        test_db.commit()

        assert tag.id is not None
        assert tag.name == "半導體"
        assert tag.color == "#3b82f6"

    def test_sector_tag_defaults(self, test_db):
        """Test sector tag default values."""
        tag = SectorTag(name="金融")
        test_db.add(tag)
        test_db.commit()

        assert tag.color == "#9ca3af"
        assert tag.keywords == ""
        assert tag.sort_order == 0

    def test_sector_tag_unique_name(self, test_db):
        """Test name unique constraint."""
        test_db.add(SectorTag(name="半導體"))
        test_db.commit()

        test_db.add(SectorTag(name="半導體"))
        with pytest.raises(Exception):
            test_db.commit()

    def test_sector_tag_repr(self, test_db):
        """Test sector tag string representation."""
        tag = SectorTag(name="電子")
        test_db.add(tag)
        test_db.commit()

        assert repr(tag) == "<SectorTag 電子>"

    def test_sector_tag_timestamps(self, test_db):
        """Test SectorTag has timestamp mixin."""
        tag = SectorTag(name="傳產")
        test_db.add(tag)
        test_db.commit()

        assert tag.created_at is not None
        assert tag.updated_at is not None
