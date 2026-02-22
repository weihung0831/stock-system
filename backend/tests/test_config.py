"""Tests for application configuration."""
import pytest
import os
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

from app.config import Settings


class TestSettingsLoading:
    """Tests for Settings configuration loading."""

    def test_settings_initialization(self, test_settings):
        """Test Settings initialization with valid values."""
        assert test_settings.DATABASE_URL == "sqlite:///:memory:"
        assert test_settings.FINMIND_TOKEN == "test_token_12345"
        assert test_settings.LLM_API_KEY == "test_llm_key"
        assert test_settings.JWT_SECRET_KEY == "test_secret_key_for_jwt_operations"

    def test_settings_default_algorithm(self, test_settings):
        """Test JWT_ALGORITHM defaults to HS256."""
        assert test_settings.JWT_ALGORITHM == "HS256"

    def test_settings_default_expire_minutes(self, test_settings):
        """Test JWT_EXPIRE_MINUTES defaults to 1440 (24 hours)."""
        assert test_settings.JWT_EXPIRE_MINUTES == 1440

    def test_settings_llm_base_url_default(self):
        """Test LLM_BASE_URL defaults to Apertis API when no env override."""
        with patch.dict(os.environ, {}, clear=True):
            s = Settings(
                _env_file=None,
                DATABASE_URL="sqlite:///:memory:",
                FINMIND_TOKEN="test",
                LLM_API_KEY="test",
                JWT_SECRET_KEY="secret",
            )
            assert s.LLM_BASE_URL == "https://api.apertis.ai/v1"

    def test_settings_llm_model_default(self):
        """Test LLM_MODEL defaults to gemini-2.5-pro when no env override."""
        with patch.dict(os.environ, {}, clear=True):
            s = Settings(
                _env_file=None,
                DATABASE_URL="sqlite:///:memory:",
                FINMIND_TOKEN="test",
                LLM_API_KEY="test",
                JWT_SECRET_KEY="secret",
            )
            assert s.LLM_MODEL == "gemini-2.5-pro"

    def test_settings_custom_llm_fields(self):
        """Test custom LLM_BASE_URL and LLM_MODEL."""
        s = Settings(
            DATABASE_URL="sqlite:///:memory:",
            FINMIND_TOKEN="test",
            LLM_API_KEY="test",
            JWT_SECRET_KEY="secret",
            LLM_BASE_URL="https://custom.api/v1",
            LLM_MODEL="gpt-4o",
        )
        assert s.LLM_BASE_URL == "https://custom.api/v1"
        assert s.LLM_MODEL == "gpt-4o"

    def test_settings_cors_origins_default(self, test_settings):
        """Test CORS_ORIGINS default value."""
        assert test_settings.CORS_ORIGINS == "http://localhost:5173"

    def test_settings_custom_jwt_expire(self):
        """Test custom JWT_EXPIRE_MINUTES."""
        settings = Settings(
            DATABASE_URL="sqlite:///:memory:",
            FINMIND_TOKEN="test",
            LLM_API_KEY="test",
            JWT_SECRET_KEY="secret",
            JWT_EXPIRE_MINUTES=60
        )

        assert settings.JWT_EXPIRE_MINUTES == 60

    def test_settings_custom_algorithm(self):
        """Test custom JWT_ALGORITHM."""
        settings = Settings(
            DATABASE_URL="sqlite:///:memory:",
            FINMIND_TOKEN="test",
            LLM_API_KEY="test",
            JWT_SECRET_KEY="secret",
            JWT_ALGORITHM="HS512"
        )

        assert settings.JWT_ALGORITHM == "HS512"

    def test_cors_origins_list_single(self, test_settings):
        """Test cors_origins_list converts single origin."""
        origins = test_settings.cors_origins_list

        assert isinstance(origins, list)
        assert len(origins) == 1
        assert "http://localhost:5173" in origins

    def test_cors_origins_list_multiple(self):
        """Test cors_origins_list converts multiple origins."""
        settings = Settings(
            DATABASE_URL="sqlite:///:memory:",
            FINMIND_TOKEN="test",
            LLM_API_KEY="test",
            JWT_SECRET_KEY="secret",
            CORS_ORIGINS="http://localhost:5173, http://localhost:3000, https://example.com"
        )

        origins = settings.cors_origins_list

        assert len(origins) == 3
        assert "http://localhost:5173" in origins
        assert "http://localhost:3000" in origins
        assert "https://example.com" in origins

    def test_cors_origins_list_strips_whitespace(self):
        """Test cors_origins_list strips whitespace."""
        settings = Settings(
            DATABASE_URL="sqlite:///:memory:",
            FINMIND_TOKEN="test",
            LLM_API_KEY="test",
            JWT_SECRET_KEY="secret",
            CORS_ORIGINS="  http://localhost:5173  ,  http://localhost:3000  "
        )

        origins = settings.cors_origins_list

        assert all(not o.startswith(" ") and not o.endswith(" ") for o in origins)
        assert len(origins) == 2

    def test_settings_required_fields(self):
        """Test that required fields must be provided."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError):
                Settings(_env_file=None)

    def test_settings_missing_database_url(self):
        """Test that DATABASE_URL is required."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError):
                Settings(
                    _env_file=None,
                    FINMIND_TOKEN="test",
                    LLM_API_KEY="test",
                    JWT_SECRET_KEY="secret"
                )

    def test_settings_missing_finmind_token(self):
        """Test that FINMIND_TOKEN is required."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError):
                Settings(
                    _env_file=None,
                    DATABASE_URL="sqlite:///:memory:",
                    LLM_API_KEY="test",
                    JWT_SECRET_KEY="secret"
                )

    def test_settings_missing_gemini_key(self):
        """Test that LLM_API_KEY is required."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError):
                Settings(
                    _env_file=None,
                    DATABASE_URL="sqlite:///:memory:",
                    FINMIND_TOKEN="test",
                    JWT_SECRET_KEY="secret"
                )

    def test_settings_missing_jwt_secret(self):
        """Test that JWT_SECRET_KEY is required."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError):
                Settings(
                    _env_file=None,
                    DATABASE_URL="sqlite:///:memory:",
                    FINMIND_TOKEN="test",
                    LLM_API_KEY="test"
                )

    def test_settings_model_config(self):
        """Test Settings model_config uses .env file."""
        assert Settings.model_config["env_file"] == ".env"

    def test_settings_from_env_file(self):
        """Test Settings can load from environment variables."""
        env_vars = {
            "DATABASE_URL": "mysql+pymysql://user:pass@localhost/db",
            "FINMIND_TOKEN": "actual_finmind_token",
            "LLM_API_KEY": "actual_gemini_key",
            "JWT_SECRET_KEY": "actual_secret",
            "JWT_ALGORITHM": "HS512",
            "JWT_EXPIRE_MINUTES": "720",
            "CORS_ORIGINS": "https://example.com"
        }

        with patch.dict(os.environ, env_vars):
            settings = Settings(_env_file=None)

            assert settings.DATABASE_URL == env_vars["DATABASE_URL"]
            assert settings.FINMIND_TOKEN == env_vars["FINMIND_TOKEN"]
            assert settings.LLM_API_KEY == env_vars["LLM_API_KEY"]
            assert settings.JWT_SECRET_KEY == env_vars["JWT_SECRET_KEY"]

    def test_settings_type_validation(self):
        """Test Settings validates field types."""
        with pytest.raises(ValidationError):
            Settings(
                DATABASE_URL="sqlite:///:memory:",
                FINMIND_TOKEN="test",
                LLM_API_KEY="test",
                JWT_SECRET_KEY="secret",
                JWT_EXPIRE_MINUTES="invalid_number"  # Should be int
            )

    def test_settings_database_url_variations(self):
        """Test Settings accepts different database URL formats."""
        test_urls = [
            "sqlite:///:memory:",
            "sqlite:///./test.db",
            "mysql+pymysql://user:pass@localhost/db",
            "postgresql://user:pass@localhost/db"
        ]

        for url in test_urls:
            settings = Settings(
                DATABASE_URL=url,
                FINMIND_TOKEN="test",
                LLM_API_KEY="test",
                JWT_SECRET_KEY="secret"
            )

            assert settings.DATABASE_URL == url

    def test_settings_all_string_fields(self):
        """Test all token/key fields are strings."""
        settings = Settings(
            DATABASE_URL="sqlite:///:memory:",
            FINMIND_TOKEN="test_token",
            LLM_API_KEY="test_key",
            JWT_SECRET_KEY="test_secret",
            CORS_ORIGINS="http://localhost"
        )

        assert isinstance(settings.FINMIND_TOKEN, str)
        assert isinstance(settings.LLM_API_KEY, str)
        assert isinstance(settings.JWT_SECRET_KEY, str)
        assert isinstance(settings.CORS_ORIGINS, str)
        assert isinstance(settings.DATABASE_URL, str)

    def test_settings_numeric_jwt_fields(self):
        """Test JWT numeric fields are correct types."""
        settings = Settings(
            DATABASE_URL="sqlite:///:memory:",
            FINMIND_TOKEN="test",
            LLM_API_KEY="test",
            JWT_SECRET_KEY="secret",
            JWT_EXPIRE_MINUTES=1440
        )

        assert isinstance(settings.JWT_EXPIRE_MINUTES, int)

    @pytest.mark.parametrize("expire_minutes", [1, 60, 1440, 10080])
    def test_settings_various_expire_times(self, expire_minutes):
        """Test Settings accepts various JWT expiration times."""
        settings = Settings(
            DATABASE_URL="sqlite:///:memory:",
            FINMIND_TOKEN="test",
            LLM_API_KEY="test",
            JWT_SECRET_KEY="secret",
            JWT_EXPIRE_MINUTES=expire_minutes
        )

        assert settings.JWT_EXPIRE_MINUTES == expire_minutes

    def test_cors_origins_list_consistency(self, test_settings):
        """Test cors_origins_list returns consistent results."""
        list1 = test_settings.cors_origins_list
        list2 = test_settings.cors_origins_list

        assert list1 == list2

    def test_settings_immutability_of_origins_list(self):
        """Test modifying cors_origins_list doesn't affect original."""
        settings = Settings(
            DATABASE_URL="sqlite:///:memory:",
            FINMIND_TOKEN="test",
            LLM_API_KEY="test",
            JWT_SECRET_KEY="secret",
            CORS_ORIGINS="http://localhost:5173"
        )

        list1 = settings.cors_origins_list
        list1.append("http://new-origin.com")

        list2 = settings.cors_origins_list
        assert len(list2) == 1  # Original unchanged
