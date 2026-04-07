"""Tests for portfolio monitoring endpoints."""
import pytest
from datetime import date
from unittest.mock import patch

from app.models.portfolio import Portfolio
from app.models.notification import Notification
from app.models.score_result import ScoreResult
from app.services.fugle_client import QuoteData


class TestPortfolioCRUD:
    """Tests for portfolio CRUD endpoints."""

    def test_create_portfolio(self, test_client, test_db, test_user, test_stock, jwt_token):
        resp = test_client.post(
            "/api/portfolio",
            json={
                "stock_id": "2330",
                "cost_price": 900.0,
                "quantity": 1000,
                "target_return_pct": 20.0,
            },
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["stock_id"] == "2330"
        assert data["stock_name"] == "台積電"
        assert data["cost_price"] == 900.0
        assert data["quantity"] == 1000
        assert data["target_return_pct"] == 20.0

    def test_create_duplicate_stock(self, test_client, test_db, test_user, test_stock, jwt_token):
        test_db.add(Portfolio(
            user_id=test_user.id, stock_id="2330", stock_name="台積電",
            cost_price=900, quantity=1000, target_return_pct=20,
        ))
        test_db.commit()

        resp = test_client.post(
            "/api/portfolio",
            json={"stock_id": "2330", "cost_price": 800, "quantity": 500, "target_return_pct": 10},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert resp.status_code == 400

    def test_list_portfolios(self, test_client, test_db, test_user, jwt_token):
        test_db.add(Portfolio(
            user_id=test_user.id, stock_id="2330", stock_name="台積電",
            cost_price=900, quantity=1000, target_return_pct=20,
        ))
        test_db.commit()

        resp = test_client.get(
            "/api/portfolio",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["stock_id"] == "2330"

    def test_update_portfolio(self, test_client, test_db, test_user, jwt_token):
        p = Portfolio(
            user_id=test_user.id, stock_id="2330", stock_name="台積電",
            cost_price=900, quantity=1000, target_return_pct=20,
        )
        test_db.add(p)
        test_db.commit()
        test_db.refresh(p)

        resp = test_client.put(
            f"/api/portfolio/{p.id}",
            json={"cost_price": 850.0, "target_return_pct": 15.0},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["cost_price"] == 850.0
        assert data["target_return_pct"] == 15.0
        assert data["quantity"] == 1000  # unchanged

    def test_delete_portfolio(self, test_client, test_db, test_user, jwt_token):
        p = Portfolio(
            user_id=test_user.id, stock_id="2330", stock_name="台積電",
            cost_price=900, quantity=1000, target_return_pct=20,
        )
        test_db.add(p)
        test_db.commit()
        test_db.refresh(p)

        resp = test_client.delete(
            f"/api/portfolio/{p.id}",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert resp.status_code == 204

    def test_ownership_check_update(self, test_client, test_db, test_user, test_admin_user, jwt_token):
        """Other user cannot update someone else's portfolio."""
        p = Portfolio(
            user_id=test_admin_user.id, stock_id="2330", stock_name="台積電",
            cost_price=900, quantity=1000, target_return_pct=20,
        )
        test_db.add(p)
        test_db.commit()
        test_db.refresh(p)

        resp = test_client.put(
            f"/api/portfolio/{p.id}",
            json={"cost_price": 1.0},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert resp.status_code == 404

    def test_ownership_check_delete(self, test_client, test_db, test_user, test_admin_user, jwt_token):
        """Other user cannot delete someone else's portfolio."""
        p = Portfolio(
            user_id=test_admin_user.id, stock_id="2330", stock_name="台積電",
            cost_price=900, quantity=1000, target_return_pct=20,
        )
        test_db.add(p)
        test_db.commit()
        test_db.refresh(p)

        resp = test_client.delete(
            f"/api/portfolio/{p.id}",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert resp.status_code == 404

    def test_unauthenticated_access(self, test_client, test_db):
        resp = test_client.get("/api/portfolio")
        assert resp.status_code in (401, 403)


class TestPortfolioRealtime:
    """Tests for real-time portfolio data endpoint."""

    @patch("app.services.portfolio_monitor.get_quotes")
    @patch("app.services.portfolio_monitor.is_quote_available", return_value=True)
    @patch("app.services.portfolio_monitor.is_market_open", return_value=True)
    def test_realtime_with_quotes(self, mock_market, mock_quote_avail, mock_quotes, test_client, test_db, test_user, jwt_token):
        test_db.add(Portfolio(
            user_id=test_user.id, stock_id="2330", stock_name="台積電",
            cost_price=900, quantity=1000, target_return_pct=20,
        ))
        test_db.commit()

        mock_quotes.return_value = {
            "2330": QuoteData(price=1000.0, change=10.0, change_pct=1.0, name="台積電"),
        }

        resp = test_client.get(
            "/api/portfolio/realtime",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_market_open"] is True
        assert data["is_realtime"] is True
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert item["current_price"] == 1000.0
        assert item["profit_pct"] == pytest.approx(11.11, abs=0.01)
        assert item["target_reached"] is False

    @patch("app.services.portfolio_monitor.get_quotes")
    @patch("app.services.portfolio_monitor.is_quote_available", return_value=False)
    @patch("app.services.portfolio_monitor.is_market_open", return_value=False)
    def test_realtime_market_closed(self, mock_market, mock_quote_avail, mock_quotes, test_client, test_db, test_user, test_daily_prices, jwt_token):
        test_db.add(Portfolio(
            user_id=test_user.id, stock_id="2330", stock_name="台積電",
            cost_price=600, quantity=100, target_return_pct=5,
        ))
        test_db.commit()

        resp = test_client.get(
            "/api/portfolio/realtime",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_market_open"] is False
        assert data["is_realtime"] is False
        assert len(data["items"]) == 1
        mock_quotes.assert_not_called()

    @patch("app.services.portfolio_monitor.get_quotes")
    @patch("app.services.portfolio_monitor.is_quote_available", return_value=True)
    @patch("app.services.portfolio_monitor.is_market_open", return_value=True)
    def test_realtime_api_failure_fallback(self, mock_market, mock_quote_avail, mock_quotes, test_client, test_db, test_user, test_daily_prices, jwt_token):
        test_db.add(Portfolio(
            user_id=test_user.id, stock_id="2330", stock_name="台積電",
            cost_price=600, quantity=100, target_return_pct=5,
        ))
        test_db.commit()

        mock_quotes.return_value = {"2330": None}

        resp = test_client.get(
            "/api/portfolio/realtime",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_realtime"] is False
        assert len(data["items"]) == 1

    @patch("app.services.portfolio_monitor.get_quotes")
    @patch("app.services.portfolio_monitor.is_quote_available", return_value=True)
    @patch("app.services.portfolio_monitor.is_market_open", return_value=True)
    def test_target_reached_creates_notification(self, mock_market, mock_quote_avail, mock_quotes, test_client, test_db, test_user, jwt_token):
        test_db.add(Portfolio(
            user_id=test_user.id, stock_id="2330", stock_name="台積電",
            cost_price=900, quantity=1000, target_return_pct=10,
        ))
        test_db.commit()

        mock_quotes.return_value = {
            "2330": QuoteData(price=1000.0, change=0, change_pct=0, name="台積電"),
        }

        resp = test_client.get(
            "/api/portfolio/realtime",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        data = resp.json()
        assert len(data["new_alerts"]) == 1
        assert data["new_alerts"][0]["stock_id"] == "2330"

        notif = test_db.query(Notification).first()
        assert notif is not None
        assert notif.type == "target_reached"

    @patch("app.services.portfolio_monitor.get_quotes")
    @patch("app.services.portfolio_monitor.is_quote_available", return_value=True)
    @patch("app.services.portfolio_monitor.is_market_open", return_value=True)
    def test_no_duplicate_notification_same_day(self, mock_market, mock_quote_avail, mock_quotes, test_client, test_db, test_user, jwt_token):
        p = Portfolio(
            user_id=test_user.id, stock_id="2330", stock_name="台積電",
            cost_price=900, quantity=1000, target_return_pct=10,
        )
        test_db.add(p)
        test_db.commit()
        test_db.refresh(p)

        test_db.add(Notification(
            user_id=test_user.id, portfolio_id=p.id,
            type="target_reached", title="test",
            created_date=date.today(),
        ))
        test_db.commit()

        mock_quotes.return_value = {
            "2330": QuoteData(price=1000.0, change=0, change_pct=0, name="台積電"),
        }

        resp = test_client.get(
            "/api/portfolio/realtime",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        data = resp.json()
        assert len(data["new_alerts"]) == 0

        count = test_db.query(Notification).filter(Notification.user_id == test_user.id).count()
        assert count == 1

    def test_realtime_empty_portfolio(self, test_client, test_db, test_user, jwt_token):
        resp = test_client.get(
            "/api/portfolio/realtime",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []

    def test_realtime_route_not_captured_by_id(self, test_client, test_db, test_user, jwt_token):
        """GET /api/portfolio/realtime should not be captured by /{id} route."""
        resp = test_client.get(
            "/api/portfolio/realtime",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert resp.status_code == 200


class TestPortfolioMomentum:
    """Tests for momentum grade tracking."""

    def test_entry_momentum_grade_set_on_create(self, test_client, test_db, test_user, test_stock, jwt_token):
        test_db.add(ScoreResult(
            stock_id="2330", score_date=date.today(),
            total_score=85, rank=1, classification="A",
        ))
        test_db.commit()

        resp = test_client.post(
            "/api/portfolio",
            json={"stock_id": "2330", "cost_price": 900, "quantity": 100, "target_return_pct": 10},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["entry_momentum_grade"] == "A"

    @patch("app.services.portfolio_monitor.get_quotes")
    @patch("app.services.portfolio_monitor.is_quote_available", return_value=True)
    @patch("app.services.portfolio_monitor.is_market_open", return_value=True)
    def test_momentum_status_in_realtime(self, mock_market, mock_quote_avail, mock_quotes, test_client, test_db, test_user, jwt_token):
        test_db.add(Portfolio(
            user_id=test_user.id, stock_id="2330", stock_name="台積電",
            cost_price=900, quantity=100, target_return_pct=20,
            entry_momentum_grade="A",
        ))
        test_db.add(ScoreResult(
            stock_id="2330", score_date=date.today(),
            total_score=50, rank=10, classification="C",
        ))
        test_db.commit()

        mock_quotes.return_value = {
            "2330": QuoteData(price=950, change=0, change_pct=0, name="台積電"),
        }

        resp = test_client.get(
            "/api/portfolio/realtime",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        item = resp.json()["items"][0]
        assert item["entry_momentum_grade"] == "A"
        assert item["current_momentum_grade"] == "C"
        assert item["momentum_status"] == "red"
