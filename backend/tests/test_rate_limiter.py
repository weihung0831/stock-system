"""Tests for rate limiting utility."""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from app.services.rate_limiter import RateLimiter


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_rate_limiter_initialization(self):
        """Test RateLimiter initialization."""
        limiter = RateLimiter(max_requests_per_hour=600)

        assert limiter.max_requests == 600
        assert limiter.request_count == 0
        assert limiter.last_request_time == 0.0

    def test_rate_limiter_custom_limit(self):
        """Test RateLimiter with custom request limit."""
        limiter = RateLimiter(max_requests_per_hour=100)

        assert limiter.max_requests == 100
        # 3600 seconds / 100 requests = 36 seconds per request
        assert limiter.request_interval == 36.0

    def test_enforce_increments_count(self):
        """Test enforce increments request count."""
        limiter = RateLimiter()

        assert limiter.request_count == 0
        limiter.enforce()
        assert limiter.request_count == 1
        limiter.enforce()
        assert limiter.request_count == 2

    def test_enforce_sets_last_request_time(self):
        """Test enforce updates last request time."""
        limiter = RateLimiter()

        before = time.time()
        limiter.enforce()
        after = time.time()

        assert before <= limiter.last_request_time <= after

    def test_enforce_throttles_rapid_requests(self):
        """Test enforce throttles requests within interval."""
        limiter = RateLimiter(max_requests_per_hour=3600)  # 1 request per second

        start = time.time()
        limiter.enforce()
        limiter.enforce()
        elapsed = time.time() - start

        # Should take ~1 second due to throttling
        assert elapsed >= 0.9  # Allow slight tolerance

    def test_retry_request_success(self):
        """Test retry_request succeeds with valid function."""
        limiter = RateLimiter()
        mock_func = Mock(return_value=pd.DataFrame({"col": [1, 2, 3]}))

        result = limiter.retry_request(mock_func, arg1="value")

        assert isinstance(result, pd.DataFrame)
        assert mock_func.called
        assert len(result) == 3

    def test_retry_request_empty_dataframe(self):
        """Test retry_request handles empty DataFrame."""
        limiter = RateLimiter()
        mock_func = Mock(return_value=pd.DataFrame())

        result = limiter.retry_request(mock_func)

        # Should retry and eventually return None
        assert result is None

    def test_retry_request_none_result(self):
        """Test retry_request handles None result."""
        limiter = RateLimiter()
        mock_func = Mock(return_value=None)

        result = limiter.retry_request(mock_func)

        assert result is None

    def test_retry_request_exception_retry(self):
        """Test retry_request retries on exception."""
        limiter = RateLimiter()

        call_count = 0

        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return pd.DataFrame({"col": [1]})

        result = limiter.retry_request(failing_func)

        assert call_count == 3
        assert isinstance(result, pd.DataFrame)

    def test_retry_request_max_retries_exceeded(self):
        """Test retry_request fails after max retries."""
        with patch("time.sleep"):
            limiter = RateLimiter()
            mock_func = Mock(side_effect=Exception("Persistent error"))
            mock_func.__name__ = "test_func"

            result = limiter.retry_request(mock_func)

            assert result is None
            assert mock_func.call_count == 3  # 3 retry attempts

    def test_retry_request_with_args_kwargs(self):
        """Test retry_request passes arguments correctly."""
        limiter = RateLimiter()

        def mock_func(arg1, arg2, kwarg1=None):
            return pd.DataFrame({
                "arg1": [arg1],
                "arg2": [arg2],
                "kwarg1": [kwarg1]
            })

        result = limiter.retry_request(
            mock_func,
            "value1",
            "value2",
            kwarg1="kwvalue"
        )

        assert isinstance(result, pd.DataFrame)
        assert result.loc[0, "arg1"] == "value1"
        assert result.loc[0, "kwarg1"] == "kwvalue"

    def test_hour_counter_resets(self):
        """Test request counter resets every hour."""
        with patch("time.time") as mock_time, \
             patch("time.sleep"):
            # Set return value BEFORE creating RateLimiter
            mock_time.return_value = 0
            limiter = RateLimiter(max_requests_per_hour=5)

            # First request
            limiter.enforce()
            assert limiter.request_count == 1

            # After 3599 seconds (still within hour)
            mock_time.return_value = 3599
            limiter.enforce()
            assert limiter.request_count == 2

            # After 3601 seconds (new hour)
            mock_time.return_value = 3601
            limiter.enforce()
            assert limiter.request_count == 1  # Reset

    def test_rate_limiter_sleep_when_limit_reached(self):
        """Test rate limiter sleeps when max requests reached."""
        with patch("time.time") as mock_time, \
             patch("time.sleep") as mock_sleep:
            # Set return value BEFORE creating RateLimiter
            mock_time.return_value = 0
            limiter = RateLimiter(max_requests_per_hour=2)
            limiter.request_count = 2  # Already at limit

            limiter.enforce()

            # Should have called sleep
            mock_sleep.assert_called()

    def test_exponential_backoff_delays(self):
        """Test retry_request uses exponential backoff."""
        with patch("time.sleep") as mock_sleep:
            limiter = RateLimiter()

            call_count = 0

            def failing_func():
                nonlocal call_count
                call_count += 1
                raise ValueError("Error")

            limiter.retry_request(failing_func)

            # Should have slept with exponential backoff
            assert mock_sleep.call_count >= 2
            calls = mock_sleep.call_args_list
            # First sleep should be less than second (exponential)
            if len(calls) >= 2:
                first_sleep = calls[0][0][0]
                second_sleep = calls[1][0][0]
                assert first_sleep < second_sleep

    def test_rate_limiter_concurrent_requests(self):
        """Test rate limiter handles multiple sequential requests."""
        limiter = RateLimiter(max_requests_per_hour=100)

        for _ in range(5):
            limiter.enforce()

        assert limiter.request_count == 5

    @pytest.mark.parametrize("max_requests", [100, 500, 1000, 2000])
    def test_rate_limiter_different_limits(self, max_requests):
        """Test rate limiter with different request limits."""
        limiter = RateLimiter(max_requests_per_hour=max_requests)

        assert limiter.max_requests == max_requests
        expected_interval = 3600 / max_requests
        assert abs(limiter.request_interval - expected_interval) < 0.01

    def test_retry_request_empty_result_after_successful(self):
        """Test retry_request continues if DataFrame becomes empty."""
        limiter = RateLimiter()

        call_count = 0

        def func_with_empty():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return pd.DataFrame({"col": [1]})
            return pd.DataFrame()  # Empty on second call

        result = limiter.retry_request(func_with_empty)

        # First call succeeds, returns data
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
