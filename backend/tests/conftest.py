"""Pytest configuration and shared fixtures for tests."""
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.config import Settings
from app.database import Base, get_db
from app.models.stock import Stock
from app.models.user import User
from app.models.daily_price import DailyPrice
from app.models.institutional import Institutional
from app.models.margin_trading import MarginTrading
from app.models.system_setting import SystemSetting
from app.models.score_result import ScoreResult
from app.models.sector_tag import SectorTag
from app.services.auth_service import hash_password


# Create in-memory SQLite database for testing
from sqlalchemy.pool import StaticPool

TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db():
    """Create test database tables and session."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_client(test_db):
    """FastAPI test client with test database override."""
    try:
        from app.main import app
    except ImportError:
        pytest.skip("App main module not available")

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_settings():
    """Test configuration settings."""
    return Settings(
        DATABASE_URL="sqlite:///:memory:",
        FINMIND_TOKEN="test_token_12345",
        LLM_API_KEY="test_llm_key",
        LLM_BASE_URL="https://api.apertis.ai/v1",
        LLM_MODEL="claude-opus-4-6",
        JWT_SECRET_KEY="test_secret_key_for_jwt_operations",
        JWT_ALGORITHM="HS256",
        JWT_EXPIRE_MINUTES=1440,
        CORS_ORIGINS="http://localhost:5173"
    )


@pytest.fixture(scope="function")
def test_user(test_db):
    """Create test user in database."""
    user = User(
        username="testuser",
        email="testuser@test.com",
        hashed_password=hash_password("password123"),
        is_admin=False,
        is_active=True,
        membership_tier="free",
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_admin_user(test_db):
    """Create test admin user in database."""
    user = User(
        username="adminuser",
        email="admin@test.com",
        hashed_password=hash_password("adminpass123"),
        is_admin=True,
        is_active=True,
        membership_tier="free",
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_stock(test_db):
    """Create test stock in database."""
    stock = Stock(
        stock_id="2330",
        stock_name="台積電",
        market="TWSE",
        industry="半導體",
        listed_date=datetime(1994, 6, 30).date()
    )
    test_db.add(stock)
    test_db.commit()
    test_db.refresh(stock)
    return stock


@pytest.fixture(scope="function")
def test_daily_prices(test_db, test_stock):
    """Create test daily price records."""
    prices = []
    base_date = datetime.now().date()

    for i in range(10):
        date = base_date - timedelta(days=i)
        price = DailyPrice(
            stock_id=test_stock.stock_id,
            trade_date=date,
            open=600.0 + i,
            high=610.0 + i,
            low=590.0 + i,
            close=605.0 + i,
            volume=1000000 + (i * 100000),
            turnover=605000000 + (i * 50000000),
            change_price=5.0,
            change_percent=0.83
        )
        prices.append(price)
        test_db.add(price)

    test_db.commit()
    return prices


@pytest.fixture(scope="function")
def mock_finmind():
    """Mock FinMind API responses."""
    with patch("app.services.finmind_collector.FinMind") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance

        # Mock stock list
        mock_instance.get_stock.return_value = {
            "data": [
                {"stock_id": "2330", "stock_name": "台積電"},
                {"stock_id": "2454", "stock_name": "聯發科"},
            ]
        }

        # Mock price data
        mock_instance.get_daily_price.return_value = {
            "data": [
                {
                    "date": "2024-01-15",
                    "open": 600,
                    "high": 610,
                    "low": 590,
                    "close": 605,
                    "volume": 1000000
                }
            ]
        }

        yield mock_instance


@pytest.fixture(scope="function")
def mock_gemini():
    """Mock Google Gemini API responses."""
    with patch("app.services.gemini_client.genai") as mock:
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "This is a mock AI-generated analysis of stock performance."
        mock_model.generate_content.return_value = mock_response

        mock.GenerativeModel.return_value = mock_model

        yield mock_model


@pytest.fixture(scope="function")
def mock_scheduler():
    """Mock APScheduler."""
    with patch("app.main.BackgroundScheduler") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def jwt_token(test_user):
    """Generate JWT token for test user."""
    from app.services.auth_service import create_access_token

    token = create_access_token({"sub": test_user.username})
    return token


@pytest.fixture(scope="function")
def admin_jwt_token(test_admin_user):
    """Generate JWT token for admin user."""
    from app.services.auth_service import create_access_token

    token = create_access_token({"sub": test_admin_user.username})
    return token


@pytest.fixture(autouse=True)
def patch_settings():
    """Patch settings for all tests."""
    with patch("app.config.settings") as mock_settings:
        mock_settings.DATABASE_URL = "sqlite:///:memory:"
        mock_settings.FINMIND_TOKEN = "test_token"
        mock_settings.LLM_API_KEY = "test_key"
        mock_settings.LLM_BASE_URL = "https://api.apertis.ai/v1"
        mock_settings.LLM_MODEL = "claude-opus-4-6"
        mock_settings.JWT_SECRET_KEY = "test_secret_key_for_jwt_operations"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_EXPIRE_MINUTES = 1440
        mock_settings.CORS_ORIGINS = "http://localhost:5173"
        mock_settings.cors_origins_list = ["http://localhost:5173"]
        yield mock_settings
