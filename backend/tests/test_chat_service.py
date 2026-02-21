"""Tests for AI chat assistant service and router."""
import pytest
from datetime import date
from unittest.mock import patch, MagicMock

from app.models.stock import Stock
from app.models.score_result import ScoreResult
from app.models.llm_report import LLMReport
from app.services.chat_service import (
    build_stock_context,
    chat_with_assistant,
    _parse_suggestions,
)


class TestBuildStockContext:
    """Tests for build_stock_context function."""

    def test_empty_database_returns_empty(self, test_db):
        """Test context is empty when no data exists."""
        context = build_stock_context(test_db)
        assert context == ""

    def test_includes_top_stocks(self, test_db, test_stock):
        """Test context includes top scored stocks."""
        score = ScoreResult(
            stock_id="2330",
            score_date=date(2026, 2, 19),
            chip_score=80.0,
            fundamental_score=75.0,
            technical_score=70.0,
            total_score=75.0,
            rank=1,
            chip_weight=0.33,
            fundamental_weight=0.34,
            technical_weight=0.33,
        )
        test_db.add(score)
        test_db.commit()

        context = build_stock_context(test_db)

        assert "2330" in context
        assert "75.0" in context
        assert "最新評分日期" in context

    def test_includes_report_date(self, test_db, test_stock):
        """Test context includes latest report info."""
        report = LLMReport(
            stock_id="2330",
            report_date=date(2026, 2, 19),
            chip_analysis="test",
            fundamental_analysis="test",
            technical_analysis="test",
            news_sentiment="中性",
            news_summary="test",
            risk_alerts=[],
            recommendation="test",
            confidence="中",
            model_used="test-model",
        )
        test_db.add(report)
        test_db.commit()

        context = build_stock_context(test_db)

        assert "最新 AI 報告日期" in context
        assert "1 份" in context

    def test_multiple_stocks_ranked(self, test_db):
        """Test top stocks are ranked by total_score desc."""
        stocks = [
            Stock(stock_id="2330", stock_name="台積電", market="TWSE"),
            Stock(stock_id="2454", stock_name="聯發科", market="TWSE"),
        ]
        test_db.add_all(stocks)
        test_db.commit()

        scores = [
            ScoreResult(
                stock_id="2330", score_date=date(2026, 2, 19),
                chip_score=90, fundamental_score=85, technical_score=80, total_score=85.0,
                rank=1, chip_weight=0.33, fundamental_weight=0.34, technical_weight=0.33,
            ),
            ScoreResult(
                stock_id="2454", score_date=date(2026, 2, 19),
                chip_score=70, fundamental_score=65, technical_score=60, total_score=65.0,
                rank=2, chip_weight=0.33, fundamental_weight=0.34, technical_weight=0.33,
            ),
        ]
        test_db.add_all(scores)
        test_db.commit()

        context = build_stock_context(test_db)

        # 台積電 (85.0) should appear before 聯發科 (65.0)
        pos_tsmc = context.index("台積電")
        pos_mtk = context.index("聯發科")
        assert pos_tsmc < pos_mtk


class TestChatWithAssistant:
    """Tests for chat_with_assistant function."""

    def test_returns_reply_on_success(self, test_db):
        """Test successful chat returns reply text."""
        mock_llm = MagicMock()
        mock_llm.generate_chat.return_value = "這是測試回覆"

        messages = [{"role": "user", "content": "你好"}]
        reply, suggestions = chat_with_assistant(test_db, mock_llm, messages)

        assert reply == "這是測試回覆"
        assert suggestions == []
        mock_llm.generate_chat.assert_called_once()

    def test_returns_none_on_failure(self, test_db):
        """Test returns None when LLM fails."""
        mock_llm = MagicMock()
        mock_llm.generate_chat.return_value = None

        messages = [{"role": "user", "content": "test"}]
        reply, suggestions = chat_with_assistant(test_db, mock_llm, messages)

        assert reply is None
        assert suggestions == []

    def test_returns_suggestions_when_present(self, test_db):
        """Test suggestions are parsed from LLM response."""
        mock_llm = MagicMock()
        mock_llm.generate_chat.return_value = (
            "這是回覆內容\n\n<<SUGGESTIONS>>\n"
            "台積電的技術面如何？\n"
            "外資近期買賣超趨勢？\n"
            "推薦其他半導體股？"
        )

        messages = [{"role": "user", "content": "分析2330"}]
        reply, suggestions = chat_with_assistant(test_db, mock_llm, messages)

        assert reply == "這是回覆內容"
        assert len(suggestions) == 3
        assert "台積電的技術面如何？" in suggestions

    def test_system_prompt_includes_context(self, test_db, test_stock):
        """Test system prompt contains stock context when data exists."""
        score = ScoreResult(
            stock_id="2330", score_date=date(2026, 2, 19),
            chip_score=80, fundamental_score=75, technical_score=70, total_score=75.0,
            rank=1, chip_weight=0.33, fundamental_weight=0.34, technical_weight=0.33,
        )
        test_db.add(score)
        test_db.commit()

        mock_llm = MagicMock()
        mock_llm.generate_chat.return_value = "reply"

        chat_with_assistant(test_db, mock_llm, [{"role": "user", "content": "hi"}])

        # Verify system prompt passed to LLM contains stock data
        call_args = mock_llm.generate_chat.call_args
        system_prompt = call_args[0][0]
        assert "2330" in system_prompt
        assert "AI 投資小幫手" in system_prompt

    def test_passes_messages_to_llm(self, test_db):
        """Test conversation history is passed correctly."""
        mock_llm = MagicMock()
        mock_llm.generate_chat.return_value = "ok"

        messages = [
            {"role": "user", "content": "問題1"},
            {"role": "assistant", "content": "回答1"},
            {"role": "user", "content": "問題2"},
        ]
        chat_with_assistant(test_db, mock_llm, messages)

        call_args = mock_llm.generate_chat.call_args
        passed_messages = call_args[0][1]
        assert len(passed_messages) == 3
        assert passed_messages[0]["content"] == "問題1"


class TestParseSuggestions:
    """Tests for _parse_suggestions helper."""

    def test_no_delimiter_returns_empty(self):
        reply, suggestions = _parse_suggestions("普通回覆沒有建議")
        assert reply == "普通回覆沒有建議"
        assert suggestions == []

    def test_parses_suggestions_correctly(self):
        raw = "回覆內容\n<<SUGGESTIONS>>\n• 問題一\n• 問題二\n• 問題三"
        reply, suggestions = _parse_suggestions(raw)
        assert reply == "回覆內容"
        assert suggestions == ["問題一", "問題二", "問題三"]

    def test_limits_to_three_suggestions(self):
        raw = "回覆\n<<SUGGESTIONS>>\n問題1\n問題2\n問題3\n問題4\n問題5"
        _, suggestions = _parse_suggestions(raw)
        assert len(suggestions) == 3

    def test_filters_short_suggestions(self):
        raw = "回覆\n<<SUGGESTIONS>>\nok\n這是一個合理的問題嗎？\n好"
        _, suggestions = _parse_suggestions(raw)
        assert len(suggestions) == 1
        assert suggestions[0] == "這是一個合理的問題嗎？"


class TestChatRouter:
    """Tests for POST /api/chat endpoint."""

    def test_chat_requires_auth(self, test_client):
        """Test chat endpoint requires authentication."""
        response = test_client.post("/api/chat", json={
            "messages": [{"role": "user", "content": "hello"}]
        })
        assert response.status_code in (401, 403)

    @patch("app.routers.chat.LLMClient")
    def test_chat_success(self, mock_llm_cls, test_client, jwt_token):
        """Test successful chat response with suggestions."""
        mock_instance = MagicMock()
        mock_instance.generate_chat.return_value = (
            "AI 回覆內容\n\n<<SUGGESTIONS>>\n延伸問題一\n延伸問題二"
        )
        mock_llm_cls.return_value = mock_instance

        response = test_client.post(
            "/api/chat",
            json={"messages": [{"role": "user", "content": "推薦哪些股票？"}]},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["reply"] == "AI 回覆內容"
        assert len(data["suggestions"]) == 2

    @patch("app.routers.chat.LLMClient")
    def test_chat_llm_failure_returns_502(self, mock_llm_cls, test_client, jwt_token):
        """Test 502 when LLM service fails."""
        mock_instance = MagicMock()
        mock_instance.generate_chat.return_value = None
        mock_llm_cls.return_value = mock_instance

        response = test_client.post(
            "/api/chat",
            json={"messages": [{"role": "user", "content": "test"}]},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

        assert response.status_code == 502

    def test_chat_empty_messages_rejected(self, test_client, jwt_token):
        """Test empty messages list is rejected."""
        response = test_client.post(
            "/api/chat",
            json={"messages": []},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 422

    def test_chat_message_too_long_rejected(self, test_client, jwt_token):
        """Test message exceeding max length is rejected."""
        long_content = "x" * 5001
        response = test_client.post(
            "/api/chat",
            json={"messages": [{"role": "user", "content": long_content}]},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 422

    def test_chat_invalid_role_rejected(self, test_client, jwt_token):
        """Test invalid message role is rejected."""
        response = test_client.post(
            "/api/chat",
            json={"messages": [{"role": "system", "content": "hack"}]},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 422

    @patch("app.routers.chat.LLMClient")
    def test_chat_multi_turn_conversation(self, mock_llm_cls, test_client, jwt_token):
        """Test multi-turn conversation is accepted."""
        mock_instance = MagicMock()
        mock_instance.generate_chat.return_value = "第二輪回覆"
        mock_llm_cls.return_value = mock_instance

        response = test_client.post(
            "/api/chat",
            json={"messages": [
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "你好！有什麼可以幫你？"},
                {"role": "user", "content": "推薦股票"},
            ]},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

        assert response.status_code == 200
        assert response.json()["reply"] == "第二輪回覆"

    @patch("app.routers.chat.chat_rate_limiter")
    def test_chat_rate_limit_returns_429(self, mock_limiter, test_client, jwt_token):
        """Test 429 when rate limiter blocks request."""
        mock_limiter.check.return_value = (False, "發送太頻繁，請等 30 秒後再試。", {"daily_remaining": 0, "minute_remaining": 0})

        response = test_client.post(
            "/api/chat",
            json={"messages": [{"role": "user", "content": "test"}]},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

        assert response.status_code == 429
        assert "發送太頻繁" in response.json()["detail"]

    @patch("app.routers.chat.chat_rate_limiter")
    @patch("app.routers.chat.LLMClient")
    def test_chat_allowed_when_rate_ok(self, mock_llm_cls, mock_limiter, test_client, jwt_token):
        """Test request proceeds when rate limiter allows."""
        mock_limiter.check.return_value = (True, "", {"daily_remaining": 9, "minute_remaining": 2})
        mock_instance = MagicMock()
        mock_instance.generate_chat.return_value = "ok"
        mock_llm_cls.return_value = mock_instance

        response = test_client.post(
            "/api/chat",
            json={"messages": [{"role": "user", "content": "test"}]},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

        assert response.status_code == 200
