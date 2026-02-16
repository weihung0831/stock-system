"""Tests for stock data service."""
import pytest
from datetime import date, timedelta
from decimal import Decimal

from app.services.stock_service import (
    get_stocks,
    get_stock_prices,
    get_stock_institutional,
    get_stock_margin
)
from app.models.stock import Stock
from app.models.daily_price import DailyPrice
from app.models.institutional import Institutional
from app.models.margin_trading import MarginTrading


class TestGetStocks:
    """Tests for get_stocks function."""

    def test_get_stocks_empty_database(self, test_db):
        """Test getting stocks from empty database."""
        stocks, total = get_stocks(test_db)

        assert len(stocks) == 0
        assert total == 0

    def test_get_stocks_with_records(self, test_db):
        """Test getting stocks with records in database."""
        # Add stocks
        stock1 = Stock(stock_id="2330", stock_name="台積電", market="TWSE")
        stock2 = Stock(stock_id="2454", stock_name="聯發科", market="TWSE")
        test_db.add_all([stock1, stock2])
        test_db.commit()

        stocks, total = get_stocks(test_db)

        assert len(stocks) == 2
        assert total == 2

    def test_get_stocks_pagination_skip(self, test_db):
        """Test pagination with skip parameter."""
        # Add 5 stocks
        for i in range(5):
            stock = Stock(stock_id=f"000{i}", stock_name=f"Stock{i}", market="TWSE")
            test_db.add(stock)
        test_db.commit()

        stocks, total = get_stocks(test_db, skip=2, limit=2)

        assert len(stocks) == 2
        assert total == 5

    def test_get_stocks_pagination_limit(self, test_db):
        """Test pagination with limit parameter."""
        for i in range(10):
            stock = Stock(stock_id=f"100{i}", stock_name=f"Company{i}", market="TWSE")
            test_db.add(stock)
        test_db.commit()

        stocks, total = get_stocks(test_db, limit=3)

        assert len(stocks) == 3
        assert total == 10

    def test_get_stocks_search_by_id(self, test_db):
        """Test searching stocks by stock_id."""
        stock1 = Stock(stock_id="2330", stock_name="台積電", market="TWSE")
        stock2 = Stock(stock_id="2454", stock_name="聯發科", market="TWSE")
        test_db.add_all([stock1, stock2])
        test_db.commit()

        stocks, total = get_stocks(test_db, search="2330")

        assert len(stocks) == 1
        assert stocks[0].stock_id == "2330"
        assert total == 1

    def test_get_stocks_search_by_name(self, test_db):
        """Test searching stocks by stock_name."""
        stock1 = Stock(stock_id="2330", stock_name="台積電", market="TWSE")
        stock2 = Stock(stock_id="2454", stock_name="聯發科", market="TWSE")
        test_db.add_all([stock1, stock2])
        test_db.commit()

        stocks, total = get_stocks(test_db, search="台積")

        assert len(stocks) == 1
        assert stocks[0].stock_name == "台積電"

    def test_get_stocks_search_partial_match(self, test_db):
        """Test search uses partial matching."""
        stock1 = Stock(stock_id="2330", stock_name="台積電", market="TWSE")
        stock2 = Stock(stock_id="2454", stock_name="聯發科", market="TWSE")
        test_db.add_all([stock1, stock2])
        test_db.commit()

        stocks, total = get_stocks(test_db, search="聯")

        assert len(stocks) == 1
        assert stocks[0].stock_name == "聯發科"

    def test_get_stocks_search_no_results(self, test_db):
        """Test search returns empty when no matches."""
        stock = Stock(stock_id="2330", stock_name="台積電", market="TWSE")
        test_db.add(stock)
        test_db.commit()

        stocks, total = get_stocks(test_db, search="nonexistent")

        assert len(stocks) == 0
        assert total == 0


class TestGetStockPrices:
    """Tests for get_stock_prices function."""

    def test_get_stock_prices_empty(self, test_db, test_stock):
        """Test getting prices for stock with no data."""
        prices = get_stock_prices(test_db, "2330")

        assert len(prices) == 0

    def test_get_stock_prices_with_data(self, test_db, test_daily_prices):
        """Test getting prices with data."""
        stock_id = test_daily_prices[0].stock_id
        prices = get_stock_prices(test_db, stock_id)

        assert len(prices) == 10

    def test_get_stock_prices_ordered_by_date_desc(self, test_db, test_daily_prices):
        """Test prices are ordered by date descending."""
        stock_id = test_daily_prices[0].stock_id
        prices = get_stock_prices(test_db, stock_id)

        for i in range(len(prices) - 1):
            assert prices[i].trade_date >= prices[i + 1].trade_date

    def test_get_stock_prices_date_filter_start(self, test_db, test_stock):
        """Test filtering prices by start date."""
        base_date = date.today()
        for i in range(5):
            date_val = base_date - timedelta(days=i)
            price = DailyPrice(
                stock_id=test_stock.stock_id,
                trade_date=date_val,
                open=600,
                high=610,
                low=590,
                close=605,
                volume=1000000
            )
            test_db.add(price)
        test_db.commit()

        filter_date = base_date - timedelta(days=2)
        prices = get_stock_prices(test_db, test_stock.stock_id, start_date=filter_date)

        assert len(prices) == 3  # Today, day1, day2

    def test_get_stock_prices_date_filter_end(self, test_db, test_stock):
        """Test filtering prices by end date."""
        base_date = date.today()
        for i in range(5):
            date_val = base_date - timedelta(days=i)
            price = DailyPrice(
                stock_id=test_stock.stock_id,
                trade_date=date_val,
                open=600,
                high=610,
                low=590,
                close=605,
                volume=1000000
            )
            test_db.add(price)
        test_db.commit()

        filter_date = base_date - timedelta(days=2)
        prices = get_stock_prices(test_db, test_stock.stock_id, end_date=filter_date)

        assert len(prices) == 3  # day2, day3, day4

    def test_get_stock_prices_date_filter_range(self, test_db, test_stock):
        """Test filtering prices by date range."""
        base_date = date.today()
        for i in range(10):
            date_val = base_date - timedelta(days=i)
            price = DailyPrice(
                stock_id=test_stock.stock_id,
                trade_date=date_val,
                open=600,
                high=610,
                low=590,
                close=605,
                volume=1000000
            )
            test_db.add(price)
        test_db.commit()

        start = base_date - timedelta(days=5)
        end = base_date - timedelta(days=2)
        prices = get_stock_prices(
            test_db,
            test_stock.stock_id,
            start_date=start,
            end_date=end
        )

        assert all(start <= p.trade_date <= end for p in prices)

    def test_get_stock_prices_nonexistent_stock(self, test_db):
        """Test getting prices for nonexistent stock."""
        prices = get_stock_prices(test_db, "9999")

        assert len(prices) == 0


class TestGetStockInstitutional:
    """Tests for get_stock_institutional function."""

    def test_get_stock_institutional_empty(self, test_db, test_stock):
        """Test getting institutional data with no records."""
        data = get_stock_institutional(test_db, test_stock.stock_id)

        assert len(data) == 0

    def test_get_stock_institutional_with_data(self, test_db, test_stock):
        """Test getting institutional data with records."""
        inst = Institutional(
            stock_id=test_stock.stock_id,
            trade_date=date.today(),
            foreign_buy=100000,
            foreign_sell=50000,
            foreign_net=50000,
            dealer_buy=20000,
            dealer_sell=10000,
            dealer_net=10000,
            trust_buy=5000,
            trust_sell=2000,
            trust_net=3000,
            total_net=60000
        )
        test_db.add(inst)
        test_db.commit()

        data = get_stock_institutional(test_db, test_stock.stock_id)

        assert len(data) == 1
        assert data[0].stock_id == test_stock.stock_id

    def test_get_stock_institutional_ordered_desc(self, test_db, test_stock):
        """Test institutional data ordered by date descending."""
        base_date = date.today()
        for i in range(3):
            inst = Institutional(
                stock_id=test_stock.stock_id,
                trade_date=base_date - timedelta(days=i),
                foreign_buy=100000 + i,
                foreign_sell=50000,
                foreign_net=50000,
                dealer_buy=20000,
                dealer_sell=10000,
                dealer_net=10000,
                trust_buy=5000,
                trust_sell=2000,
                trust_net=3000,
                total_net=60000
            )
            test_db.add(inst)
        test_db.commit()

        data = get_stock_institutional(test_db, test_stock.stock_id)

        for i in range(len(data) - 1):
            assert data[i].trade_date >= data[i + 1].trade_date

    def test_get_stock_institutional_date_filter(self, test_db, test_stock):
        """Test filtering institutional data by date."""
        base_date = date.today()
        for i in range(5):
            inst = Institutional(
                stock_id=test_stock.stock_id,
                trade_date=base_date - timedelta(days=i),
                foreign_buy=100000,
                foreign_sell=50000,
                foreign_net=50000,
                dealer_buy=20000,
                dealer_sell=10000,
                dealer_net=10000,
                trust_buy=5000,
                trust_sell=2000,
                trust_net=3000,
                total_net=60000
            )
            test_db.add(inst)
        test_db.commit()

        start = base_date - timedelta(days=3)
        end = base_date - timedelta(days=1)
        data = get_stock_institutional(
            test_db,
            test_stock.stock_id,
            start_date=start,
            end_date=end
        )

        assert all(start <= d.trade_date <= end for d in data)


class TestGetStockMargin:
    """Tests for get_stock_margin function."""

    def test_get_stock_margin_empty(self, test_db, test_stock):
        """Test getting margin data with no records."""
        data = get_stock_margin(test_db, test_stock.stock_id)

        assert len(data) == 0

    def test_get_stock_margin_with_data(self, test_db, test_stock):
        """Test getting margin data with records."""
        margin = MarginTrading(
            stock_id=test_stock.stock_id,
            trade_date=date.today(),
            margin_buy=50000,
            margin_sell=30000,
            margin_balance=20000,
            margin_change=1000,
            short_buy=10000,
            short_sell=5000,
            short_balance=5000,
            short_change=100
        )
        test_db.add(margin)
        test_db.commit()

        data = get_stock_margin(test_db, test_stock.stock_id)

        assert len(data) == 1

    def test_get_stock_margin_ordered_desc(self, test_db, test_stock):
        """Test margin data ordered by date descending."""
        base_date = date.today()
        for i in range(3):
            margin = MarginTrading(
                stock_id=test_stock.stock_id,
                trade_date=base_date - timedelta(days=i),
                margin_buy=50000,
                margin_sell=30000,
                margin_balance=20000,
                margin_change=1000,
                short_buy=10000,
                short_sell=5000,
                short_balance=5000,
                short_change=100
            )
            test_db.add(margin)
        test_db.commit()

        data = get_stock_margin(test_db, test_stock.stock_id)

        for i in range(len(data) - 1):
            assert data[i].trade_date >= data[i + 1].trade_date

    def test_get_stock_margin_date_filter(self, test_db, test_stock):
        """Test filtering margin data by date."""
        base_date = date.today()
        for i in range(5):
            margin = MarginTrading(
                stock_id=test_stock.stock_id,
                trade_date=base_date - timedelta(days=i),
                margin_buy=50000,
                margin_sell=30000,
                margin_balance=20000,
                margin_change=1000,
                short_buy=10000,
                short_sell=5000,
                short_balance=5000,
                short_change=100
            )
            test_db.add(margin)
        test_db.commit()

        start = base_date - timedelta(days=2)
        data = get_stock_margin(test_db, test_stock.stock_id, start_date=start)

        assert all(d.trade_date >= start for d in data)
