"""Account settings: username and password changes (no database)."""

import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user
from app.api.routes import users
from app.core.security import hash_password, verify_password
from app.db.dependencies import get_db
from app.main import app


class FakeDb:
    def commit(self):
        pass

    def refresh(self, _obj):
        pass


class AccountSettingsTests(unittest.TestCase):
    def setUp(self):
        self.user = SimpleNamespace(
            id=7, email="person@example.com", username="person", is_active=True,
            created_at=datetime.now(UTC), hashed_password=hash_password("old-password"),
        )
        app.dependency_overrides[get_current_user] = lambda: self.user
        app.dependency_overrides[get_db] = FakeDb
        self.addCleanup(app.dependency_overrides.clear)
        self.client = TestClient(app)

    def test_username_can_be_changed(self):
        with patch.object(users, "get_user_by_username", return_value=None):
            response = self.client.patch("/users/me", json={"username": "  new-name  "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "new-name")

    def test_taken_username_is_rejected(self):
        other = SimpleNamespace(id=99)
        with patch.object(users, "get_user_by_username", return_value=other):
            response = self.client.patch("/users/me", json={"username": "taken"})
        self.assertEqual(response.status_code, 409)

    def test_password_change_requires_current_password(self):
        response = self.client.post(
            "/users/me/password", json={"current_password": "wrong", "new_password": "a-new-password"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue(verify_password("old-password", self.user.hashed_password))

    def test_password_change_succeeds(self):
        response = self.client.post(
            "/users/me/password", json={"current_password": "old-password", "new_password": "a-new-password"}
        )
        self.assertEqual(response.status_code, 204)
        self.assertTrue(verify_password("a-new-password", self.user.hashed_password))

    def test_short_new_password_is_rejected(self):
        response = self.client.post(
            "/users/me/password", json={"current_password": "old-password", "new_password": "short"}
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
