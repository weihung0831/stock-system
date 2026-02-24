"""Tests for pipeline analysis steps."""
import pytest
from unittest.mock import patch, MagicMock

from app.tasks.analysis_steps import step_hard_filter


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
