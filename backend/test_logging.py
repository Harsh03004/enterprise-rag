"""Tests for structured logging and request-ID propagation."""

import json
import logging
import unittest

from app.core.logging import JsonFormatter, RequestIdFilter, request_id_var


def _record(message="hello", **extra):
    record = logging.LogRecord("app.test", logging.INFO, __file__, 1, message, (), None)
    for key, value in extra.items():
        setattr(record, key, value)
    return record


class JsonLoggingTests(unittest.TestCase):
    def test_json_line_carries_request_id_and_extra_fields(self):
        token = request_id_var.set("req-123")
        try:
            record = _record("rag_query", latency_ms=42, status="completed")
            RequestIdFilter().filter(record)
        finally:
            request_id_var.reset(token)
        payload = json.loads(JsonFormatter().format(record))
        self.assertEqual(payload["message"], "rag_query")
        self.assertEqual(payload["request_id"], "req-123")
        self.assertEqual((payload["latency_ms"], payload["status"]), (42, "completed"))
        self.assertEqual(payload["level"], "INFO")

    def test_explicit_request_id_is_not_overwritten(self):
        record = _record(request_id="explicit")
        RequestIdFilter().filter(record)
        self.assertEqual(record.request_id, "explicit")

    def test_missing_request_id_is_dash(self):
        record = _record()
        RequestIdFilter().filter(record)
        self.assertEqual(record.request_id, "-")


class RequestIdMiddlewareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient

        from app.main import app

        cls.client = TestClient(app)

    def test_supplied_request_id_is_echoed(self):
        response = self.client.get("/health", headers={"X-Request-ID": "abc-123"})
        self.assertEqual(response.headers["X-Request-ID"], "abc-123")

    def test_unsafe_request_id_is_replaced(self):
        response = self.client.get("/health", headers={"X-Request-ID": "x" * 200})
        self.assertNotEqual(response.headers["X-Request-ID"], "x" * 200)
        self.assertEqual(len(response.headers["X-Request-ID"]), 32)


if __name__ == "__main__":
    unittest.main()
