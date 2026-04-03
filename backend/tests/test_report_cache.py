"""Tests for report generation 24h cache and created_at field."""
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest

from app.models.stock import Stock
from app.models.llm_report import LLMReport
from app.models.score_result import ScoreResult


class TestReportCacheEndpoint:
    """Integration tests for POST /api/reports/{stock_id}/generate cache logic."""

    def _seed_stock_and_score(self, db, stock_id="2330"):
        """Helper to create stock and score for report generation."""
        stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
        if not stock:
            stock = Stock(stock_id=stock_id, stock_name="台積電", market="TWSE")
            db.add(stock)
        score = ScoreResult(
            stock_id=stock_id, score_date=date.today(),
            total_score=75.0, rank=1,
        )
        db.add(score)
        db.commit()
        return stock

    def _seed_report(self, db, stock_id="2330", created_at=None):
        """Helper to create a report with specific created_at."""
        report = LLMReport(
            stock_id=stock_id,
            report_date=date.today(),
            chip_analysis="籌碼分析",
            fundamental_analysis="基本面分析",
            technical_analysis="技術面分析",
            news_sentiment="正面",
            news_summary="新聞摘要",
            risk_alerts=[],
            recommendation="建議買入",
            confidence="高",
            model_used="test-model",
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        # Override created_at after commit if needed
        if created_at:
            report.created_at = created_at
            db.commit()
            db.refresh(report)
        return report

    @patch("app.services.llm_client.LLMClient")
    def test_returns_cached_report_within_24h(
        self, mock_llm_cls, test_client, test_db, jwt_token
    ):
        """Report within 24h should return cached without calling LLM."""
        self._seed_stock_and_score(test_db)
        self._seed_report(test_db)  # Just created, within 24h

        response = test_client.post(
            "/api/reports/2330/generate",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["stock_id"] == "2330"
        assert "created_at" in data
        # LLM should NOT be called (cached report returned)
        mock_llm_cls.assert_not_called()

    @patch("app.services.llm_analyzer.LLMAnalyzer")
    @patch("app.services.llm_client.LLMClient")
    def test_generates_new_report_after_24h(
        self, mock_llm_cls, mock_analyzer_cls, test_client, test_db, jwt_token
    ):
        """Report older than 24h should trigger new LLM generation."""
        self._seed_stock_and_score(test_db)
        old_time = datetime.now() - timedelta(hours=25)
        old_report = self._seed_report(test_db, created_at=old_time)

        mock_analyzer = MagicMock()
        mock_analyzer.analyze_stock.return_value = {"id": old_report.id}
        mock_analyzer_cls.return_value = mock_analyzer

        response = test_client.post(
            "/api/reports/2330/generate",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

        assert response.status_code == 200
        mock_analyzer.analyze_stock.assert_called_once()

    def test_generate_requires_auth(self, test_client):
        """Report generation requires authentication."""
        response = test_client.post("/api/reports/2330/generate")
        assert response.status_code in (401, 403)

    def test_generate_404_unknown_stock(self, test_client, jwt_token):
        """Unknown stock returns 404."""
        response = test_client.post(
            "/api/reports/9999/generate",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 404


class TestReportResponseSchema:
    """Test that LLMReportResponse includes created_at."""

    def test_created_at_in_response(self):
        from app.schemas.report import LLMReportResponse
        fields = LLMReportResponse.model_fields
        assert "created_at" in fields
