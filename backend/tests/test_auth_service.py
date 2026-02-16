"""Tests for authentication service (password hashing and JWT tokens)."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from jose import JWTError

from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    pwd_context
)
from app.config import Settings


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_success(self):
        """Test password hashing creates valid hash."""
        plain_password = "mypassword123"
        hashed = hash_password(plain_password)

        assert hashed != plain_password
        assert len(hashed) > 0
        assert pwd_context.identify(hashed) == "bcrypt"

    def test_verify_password_success(self):
        """Test password verification succeeds with correct password."""
        plain_password = "correctpassword"
        hashed = hash_password(plain_password)

        assert verify_password(plain_password, hashed) is True

    def test_verify_password_failure(self):
        """Test password verification fails with incorrect password."""
        plain_password = "correctpassword"
        hashed = hash_password(plain_password)

        assert verify_password("wrongpassword", hashed) is False

    def test_hash_same_password_different_hashes(self):
        """Test same password produces different hashes (bcrypt randomness)."""
        password = "test123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2

    @pytest.mark.parametrize("password", [
        "simple",
        "Complex!Pass@123",
        "with spaces in it",
        "unicode_字符_test",
        "x" * 72,  # Bcrypt max length is 72 bytes
    ])
    def test_hash_various_passwords(self, password):
        """Test hashing works with various password formats."""
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True


class TestJWTTokens:
    """Tests for JWT token creation and validation."""

    def test_create_access_token_success(self, test_settings):
        """Test creating access token with valid payload."""
        with patch("app.services.auth_service.settings", test_settings):
            data = {"sub": "testuser"}
            token = create_access_token(data)

            assert isinstance(token, str)
            assert len(token) > 0
            assert token.count(".") == 2  # JWT format: header.payload.signature

    def test_decode_access_token_success(self, test_settings):
        """Test decoding valid access token."""
        with patch("app.services.auth_service.settings", test_settings):
            original_data = {"sub": "testuser"}
            token = create_access_token(original_data)

            decoded = decode_access_token(token)

            assert decoded["sub"] == "testuser"
            assert "exp" in decoded  # Should have expiration

    def test_decode_invalid_token_raises_error(self, test_settings):
        """Test decoding invalid token raises JWTError."""
        with patch("app.services.auth_service.settings", test_settings):
            invalid_token = "invalid.token.here"

            with pytest.raises(JWTError):
                decode_access_token(invalid_token)

    def test_decode_empty_token_raises_error(self, test_settings):
        """Test decoding empty token raises JWTError."""
        with patch("app.services.auth_service.settings", test_settings):
            with pytest.raises(JWTError):
                decode_access_token("")

    def test_token_contains_expiration(self, test_settings):
        """Test token includes expiration claim."""
        with patch("app.services.auth_service.settings", test_settings):
            token = create_access_token({"sub": "user123"})
            decoded = decode_access_token(token)

            assert "exp" in decoded
            assert decoded["exp"] > datetime.utcnow().timestamp()

    def test_token_expiration_respected(self, test_settings):
        """Test expired token validation fails."""
        with patch("app.services.auth_service.settings", test_settings):
            # Modify settings to expire immediately
            test_settings.JWT_EXPIRE_MINUTES = -1

            token = create_access_token({"sub": "user123"})

            with pytest.raises(JWTError):
                decode_access_token(token)

    def test_token_with_multiple_claims(self, test_settings):
        """Test token with multiple claims."""
        with patch("app.services.auth_service.settings", test_settings):
            data = {
                "sub": "user123",
                "role": "admin",
                "email": "user@example.com"
            }
            token = create_access_token(data)
            decoded = decode_access_token(token)

            assert decoded["sub"] == "user123"
            assert decoded["role"] == "admin"
            assert decoded["email"] == "user@example.com"

    def test_token_payload_preserved(self, test_settings):
        """Test token payload is preserved through encode/decode."""
        with patch("app.services.auth_service.settings", test_settings):
            original = {"sub": "testuser", "admin": True}
            token = create_access_token(original)
            decoded = decode_access_token(token)

            assert decoded["sub"] == original["sub"]
            assert decoded["admin"] == original["admin"]

    def test_wrong_secret_key_fails_decode(self, test_settings):
        """Test decoding token with wrong secret key fails."""
        with patch("app.services.auth_service.settings", test_settings):
            token = create_access_token({"sub": "user"})

            # Create new settings with different secret
            test_settings.JWT_SECRET_KEY = "different_secret_key_value"

            with pytest.raises(JWTError):
                decode_access_token(token)
