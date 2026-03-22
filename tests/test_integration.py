from __future__ import annotations

import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from fastapi_silk import SQLDebugMiddleware, setup_sql_profiler, silk_router
from fastapi_silk.storage import recent_queries


def build_app() -> FastAPI:
    app = FastAPI()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    setup_sql_profiler(engine)
    app.add_middleware(SQLDebugMiddleware)
    app.include_router(silk_router)

    with engine.begin() as conn:
        conn.execute(
            text("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")
        )
        conn.execute(text("INSERT INTO users (name) VALUES ('alice')"))

    @app.get("/with-query")
    def with_query() -> dict[str, bool]:
        with engine.connect() as conn:
            conn.execute(text("SELECT id, name FROM users"))
        return {"ok": True}

    @app.get("/no-query")
    def no_query() -> dict[str, bool]:
        return {"ok": True}

    return app


class TestSQLProfilerIntegration(unittest.TestCase):
    def setUp(self) -> None:
        recent_queries.clear()

    def test_headers_exist_and_count_queries(self) -> None:
        app = build_app()

        with TestClient(app) as client:
            response = client.get("/with-query")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-DB-Queries"], "1")
        self.assertTrue(response.headers["X-DB-Time"].endswith("s"))
        self.assertTrue(response.headers["X-Total-Time"].endswith("s"))

    def test_request_state_is_reset_between_requests(self) -> None:
        app = build_app()

        with TestClient(app) as client:
            first = client.get("/with-query")
            second = client.get("/no-query")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.headers["X-DB-Queries"], "1")
        self.assertEqual(second.headers["X-DB-Queries"], "0")

    def test_recent_api_includes_database_schema_table_trigger_counts(self) -> None:
        app = build_app()

        with TestClient(app) as client:
            run_response = client.get("/with-query")
            recent_response = client.get("/_silk/api/recent")

        self.assertEqual(run_response.status_code, 200)
        self.assertEqual(recent_response.status_code, 200)

        payload = recent_response.json()
        self.assertIn("recent", payload)
        self.assertGreater(len(payload["recent"]), 0)

        target_entry = next(
            entry for entry in payload["recent"] if entry["path"] == "/with-query"
        )

        self.assertEqual(target_entry["database_trigger_count"], 1)
        self.assertEqual(target_entry["schema_trigger_count"], 0)
        self.assertEqual(target_entry["table_trigger_count"], 1)
        self.assertEqual(target_entry["table_hits"].get("users"), 1)


if __name__ == "__main__":
    unittest.main()
