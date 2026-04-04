"""Tests for notification endpoints."""
import pytest
from datetime import date

from app.models.notification import Notification
from app.models.portfolio import Portfolio


class TestNotificationEndpoints:
    """Tests for notification API."""

    def _create_notification(self, test_db, user_id, is_read=False):
        n = Notification(
            user_id=user_id,
            type="target_reached",
            title="Test notification",
            message="Test message",
            is_read=is_read,
            created_date=date.today(),
        )
        test_db.add(n)
        test_db.commit()
        test_db.refresh(n)
        return n

    def test_list_notifications(self, test_client, test_db, test_user, jwt_token):
        self._create_notification(test_db, test_user.id)
        self._create_notification(test_db, test_user.id, is_read=True)

        resp = test_client.get(
            "/api/notifications",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_unread_count(self, test_client, test_db, test_user, jwt_token):
        self._create_notification(test_db, test_user.id)
        self._create_notification(test_db, test_user.id)
        self._create_notification(test_db, test_user.id, is_read=True)

        resp = test_client.get(
            "/api/notifications/unread-count",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 2

    def test_mark_read(self, test_client, test_db, test_user, jwt_token):
        n = self._create_notification(test_db, test_user.id)

        resp = test_client.put(
            f"/api/notifications/{n.id}/read",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["is_read"] is True

    def test_mark_all_read(self, test_client, test_db, test_user, jwt_token):
        self._create_notification(test_db, test_user.id)
        self._create_notification(test_db, test_user.id)

        resp = test_client.put(
            "/api/notifications/batch-read",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert resp.status_code == 200

        count_resp = test_client.get(
            "/api/notifications/unread-count",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert count_resp.json()["count"] == 0

    def test_ownership_check(self, test_client, test_db, test_user, test_admin_user, jwt_token):
        """User cannot mark another user's notification as read."""
        n = self._create_notification(test_db, test_admin_user.id)

        resp = test_client.put(
            f"/api/notifications/{n.id}/read",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert resp.status_code == 404

    def test_unauthenticated_access(self, test_client, test_db):
        resp = test_client.get("/api/notifications")
        assert resp.status_code in (401, 403)

    def test_unread_count_only_own_notifications(self, test_client, test_db, test_user, test_admin_user, jwt_token):
        """Unread count only counts own notifications."""
        self._create_notification(test_db, test_user.id)
        self._create_notification(test_db, test_admin_user.id)
        self._create_notification(test_db, test_admin_user.id)

        resp = test_client.get(
            "/api/notifications/unread-count",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert resp.json()["count"] == 1
