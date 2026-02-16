"""Tests for pipeline analysis steps."""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import patch, MagicMock

from app.models.score_result import ScoreResult
from app.tasks.analysis_steps import step_llm_analysis, step_hard_filter


class TestStepLLMAnalysis:
    """Tests for step_llm_analysis function."""

    def _seed_scores(self, db, count=5, score_date=None):
        """Helper to seed ScoreResult records."""
        if score_date is None:
            score_date = date(2026, 2, 15)
        for i in range(count):
            db.add(ScoreResult(
                stock_id=str(2330 + i),
                score_date=score_date,
                chip_score=Decimal("80") - i,
                fundamental_score=Decimal("70") - i,
                technical_score=Decimal("60") - i,
                total_score=Decimal("75") - i,
                rank=i + 1,
                chip_weight=40, fundamental_weight=35, technical_weight=25,
            ))
        db.commit()

    def test_no_scores_returns_early(self, test_db):
        """Test returns early when no score results exist."""
        result = step_llm_analysis(test_db, top_n=10)

        assert result["success"] is True
        assert result["reports_count"] == 0
        assert "No scores" in result["message"]

    @patch("app.tasks.analysis_steps.LLMAnalyzer")
    @patch("app.tasks.analysis_steps.LLMClient")
    def test_top_n_limits_results(self, mock_client_cls, mock_analyzer_cls, test_db):
        """Test top_n > 0 limits the number of stocks analyzed."""
        self._seed_scores(test_db, count=10)

        mock_analyzer = MagicMock()
        mock_analyzer.analyze_batch.return_value = [{"stock_id": "2330"}]
        mock_analyzer_cls.return_value = mock_analyzer

        result = step_llm_analysis(test_db, top_n=3)

        assert result["success"] is True
        # Verify analyze_batch was called with exactly 3 stocks
        call_args = mock_analyzer.analyze_batch.call_args
        assert len(call_args[0][1]) == 3

    @patch("app.tasks.analysis_steps.LLMAnalyzer")
    @patch("app.tasks.analysis_steps.LLMClient")
    def test_top_n_zero_returns_all(self, mock_client_cls, mock_analyzer_cls, test_db):
        """Test top_n=0 returns all scored stocks (no limit)."""
        self._seed_scores(test_db, count=10)

        mock_analyzer = MagicMock()
        mock_analyzer.analyze_batch.return_value = []
        mock_analyzer_cls.return_value = mock_analyzer

        result = step_llm_analysis(test_db, top_n=0)

        assert result["success"] is True
        call_args = mock_analyzer.analyze_batch.call_args
        assert len(call_args[0][1]) == 10

    @patch("app.tasks.analysis_steps.LLMAnalyzer")
    @patch("app.tasks.analysis_steps.LLMClient")
    def test_stocks_ordered_by_total_score_desc(self, mock_client_cls, mock_analyzer_cls, test_db):
        """Test stocks are passed in descending total_score order."""
        self._seed_scores(test_db, count=5)

        mock_analyzer = MagicMock()
        mock_analyzer.analyze_batch.return_value = []
        mock_analyzer_cls.return_value = mock_analyzer

        step_llm_analysis(test_db, top_n=0)

        call_args = mock_analyzer.analyze_batch.call_args
        stocks = call_args[0][1]
        scores = [s["scores"]["total"] for s in stocks]
        assert scores == sorted(scores, reverse=True)


class TestStepHardFilter:
    """Tests for step_hard_filter function."""

    @patch("app.tasks.analysis_steps.HardFilter")
    def test_hard_filter_success(self, mock_hf_cls, test_db):
        """Test step_hard_filter returns candidates on success."""
        mock_hf = MagicMock()
        mock_hf.filter_by_volume.return_value = ["2330", "2454"]
        mock_hf_cls.return_value = mock_hf

        result = step_hard_filter(test_db, "2026-02-15")

        assert result["success"] is True
        assert result["candidates"] == ["2330", "2454"]

    @patch("app.tasks.analysis_steps.HardFilter")
    def test_hard_filter_error_handling(self, mock_hf_cls, test_db):
        """Test step_hard_filter handles exceptions gracefully."""
        mock_hf = MagicMock()
        mock_hf.filter_by_volume.side_effect = RuntimeError("DB error")
        mock_hf_cls.return_value = mock_hf

        result = step_hard_filter(test_db, "2026-02-15")

        assert result["success"] is False
        assert result["candidates"] == []
