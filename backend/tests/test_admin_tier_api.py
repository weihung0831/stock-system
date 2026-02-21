"""Tests for admin tier management API."""
import pytest

from app.services.auth_service import hash_password
from app.models.user import User


class TestAdminTierApi:
    """Tests for PATCH /api/admin/users/{user_id}/tier."""

    def test_admin_upgrade_user(self, test_client, test_db, test_user, test_admin_user, admin_jwt_token):
        resp = test_client.patch(
            f"/api/admin/users/{test_user.id}/tier",
            json={"membership_tier": "premium"},
            headers={"Authorization": f"Bearer {admin_jwt_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["membership_tier"] == "premium"

    def test_admin_downgrade_user(self, test_client, test_db, test_user, test_admin_user, admin_jwt_token):
        # First upgrade
        test_user.membership_tier = "premium"
        test_db.commit()

        resp = test_client.patch(
            f"/api/admin/users/{test_user.id}/tier",
            json={"membership_tier": "free"},
            headers={"Authorization": f"Bearer {admin_jwt_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["membership_tier"] == "free"

    def test_non_admin_cannot_change_tier(self, test_client, test_db, test_user, jwt_token):
        resp = test_client.patch(
            f"/api/admin/users/{test_user.id}/tier",
            json={"membership_tier": "premium"},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert resp.status_code == 403

    def test_admin_invalid_tier(self, test_client, test_db, test_user, test_admin_user, admin_jwt_token):
        resp = test_client.patch(
            f"/api/admin/users/{test_user.id}/tier",
            json={"membership_tier": "gold"},
            headers={"Authorization": f"Bearer {admin_jwt_token}"},
        )
        assert resp.status_code == 422

    def test_admin_user_not_found(self, test_client, test_db, test_admin_user, admin_jwt_token):
        resp = test_client.patch(
            "/api/admin/users/99999/tier",
            json={"membership_tier": "premium"},
            headers={"Authorization": f"Bearer {admin_jwt_token}"},
        )
        assert resp.status_code == 404
