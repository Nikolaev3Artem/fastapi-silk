from __future__ import annotations

import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from fastapi_silk import SQLDebugMiddleware, setup_sql_profiler


def build_app() -> FastAPI:
    app = FastAPI()
    engine = create_engine("sqlite://")

    setup_sql_profiler(engine)
    app.add_middleware(SQLDebugMiddleware)

    @app.get("/with-query")
    def with_query() -> dict[str, bool]:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"ok": True}

    @app.get("/no-query")
    def no_query() -> dict[str, bool]:
        return {"ok": True}

    return app


class TestSQLProfilerIntegration(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
