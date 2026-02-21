"""Tests for user registration endpoint."""
import pytest

from app.services.auth_service import hash_password
from app.models.user import User


class TestRegisterEndpoint:
    """Tests for POST /api/auth/register."""

    def test_register_success(self, test_client, test_db):
        resp = test_client.post("/api/auth/register", json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "StrongPass1",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert data["membership_tier"] == "free"
        assert data["is_active"] is True

    def test_register_duplicate_username(self, test_client, test_db, test_user):
        resp = test_client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "other@example.com",
            "password": "StrongPass1",
        })
        assert resp.status_code == 409
        assert "帳號" in resp.json()["detail"]

    def test_register_duplicate_email(self, test_client, test_db, test_user):
        resp = test_client.post("/api/auth/register", json={
            "username": "anotheruser",
            "email": "testuser@test.com",
            "password": "StrongPass1",
        })
        assert resp.status_code == 409
        assert "Email" in resp.json()["detail"]

    def test_register_duplicate_email_case_insensitive(self, test_client, test_db, test_user):
        resp = test_client.post("/api/auth/register", json={
            "username": "anotheruser",
            "email": "TestUser@Test.COM",
            "password": "StrongPass1",
        })
        assert resp.status_code == 409

    def test_register_password_without_uppercase_allowed(self, test_client, test_db):
        """Password without uppercase is accepted (only min 8 chars required)."""
        resp = test_client.post("/api/auth/register", json={
            "username": "user1",
            "email": "u1@example.com",
            "password": "weakpass1",
        })
        assert resp.status_code == 201

    def test_register_password_without_digit_allowed(self, test_client, test_db):
        """Password without digit is accepted (only min 8 chars required)."""
        resp = test_client.post("/api/auth/register", json={
            "username": "user2",
            "email": "u2@example.com",
            "password": "weakpasss",
        })
        assert resp.status_code == 201

    def test_register_short_password(self, test_client, test_db):
        resp = test_client.post("/api/auth/register", json={
            "username": "user3",
            "email": "u3@example.com",
            "password": "Ab1",
        })
        assert resp.status_code == 422

    def test_register_invalid_email(self, test_client, test_db):
        resp = test_client.post("/api/auth/register", json={
            "username": "user4",
            "email": "not-an-email",
            "password": "StrongPass1",
        })
        assert resp.status_code == 422

    def test_register_missing_fields(self, test_client, test_db):
        resp = test_client.post("/api/auth/register", json={})
        assert resp.status_code == 422
