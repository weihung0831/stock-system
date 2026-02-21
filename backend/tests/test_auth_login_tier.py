"""Tests for JWT tier embedding in login."""
import pytest

from app.services.auth_service import hash_password, decode_access_token
from app.models.user import User


class TestLoginJwtTier:
    """Tests for tier field in JWT token after login."""

    def test_login_jwt_contains_tier(self, test_client, test_db, test_user):
        resp = test_client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "password123",
        })
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        payload = decode_access_token(token)
        assert "tier" in payload
        assert payload["tier"] == "free"

    def test_login_jwt_tier_matches_premium(self, test_client, test_db):
        user = User(
            username="premiumuser",
            email="premium@test.com",
            hashed_password=hash_password("StrongPass1"),
            membership_tier="premium",
        )
        test_db.add(user)
        test_db.commit()

        resp = test_client.post("/api/auth/login", json={
            "username": "premiumuser",
            "password": "StrongPass1",
        })
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        payload = decode_access_token(token)
        assert payload["tier"] == "premium"
