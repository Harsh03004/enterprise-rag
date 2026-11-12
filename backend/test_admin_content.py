"""Admin content endpoints: access control and filter validation (no database)."""

import unittest
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.dependencies import get_current_admin
from app.db.dependencies import get_db
from app.main import app


class AdminContentTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(app.dependency_overrides.clear)

    def test_requires_authentication(self):
        self.assertEqual(self.client.get("/admin/documents").status_code, 401)
        self.assertEqual(self.client.get("/admin/collections").status_code, 401)

    def test_unknown_status_filter_is_rejected(self):
        app.dependency_overrides[get_current_admin] = lambda: SimpleNamespace(id=1, email="admin@example.com")
        app.dependency_overrides[get_db] = lambda: None
        response = self.client.get("/admin/documents", params={"status": "bogus"})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
