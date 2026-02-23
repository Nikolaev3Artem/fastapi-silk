from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import Engine

from fastapi_silk import SQLDebugMiddleware, silk_router


def test_ui_routes_populate_recent(engine: Engine):
    """Create a small app, run a DB query and ensure the silk UI reports it."""
    app = FastAPI()
    app.add_middleware(SQLDebugMiddleware)
    app.include_router(silk_router)

    @app.get("/run")
    def run_query():
        # execute a simple query so the profiler records it for this request
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"ok": True}

    client = TestClient(app)

    resp = client.get("/run")
    assert resp.status_code == 200

    # JSON API should contain at least one entry for the /run path
    resp2 = client.get("/_silk/api/recent")
    assert resp2.status_code == 200
    payload = resp2.json()
    assert "recent" in payload
    recent = payload["recent"]
    assert isinstance(recent, list)

    # find an entry for our route
    entries = [r for r in recent if r.get("path") == "/run"]
    assert entries, "expected at least one recent entry for /run"
    entry = entries[-1]
    assert entry["method"] == "GET"
    assert entry["queries"]
    assert "sql" in entry["queries"][0]

    # the HTML page should render (basic smoke test)
    resp3 = client.get("/_silk/")
    assert resp3.status_code == 200
    assert "Recent DB Queries" in resp3.text
