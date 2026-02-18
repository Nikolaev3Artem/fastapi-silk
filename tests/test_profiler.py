from typing import Any

import pytest
from sqlalchemy import create_engine, text

from fastapi_silk.profiler import setup_sql_profiler
from fastapi_silk.storage import request_queries


@pytest.fixture
def engine():
    """Create an in-memory SQLite engine with SQL profiler attached."""
    engine = create_engine("sqlite:///:memory:")
    setup_sql_profiler(engine)
    return engine


@pytest.fixture(autouse=True)
def reset_queries() -> None:
    """Ensure query storage is clean before and after each test."""
    request_queries.set([])
    try:
        yield
    finally:
        request_queries.set([])


@pytest.fixture(params=["SELECT 1"])
def sql_query(request: pytest.FixtureRequest) -> str:
    """SQL statements to execute, easily extendable/parameterized."""
    return request.param


@pytest.fixture
def queries() -> list[dict[str, Any]]:
    """Expose captured SQL queries for assertions."""
    return request_queries.get()


def test_profiler_captures_query(
    engine,
    sql_query: str,
    queries: list[dict[str, Any]],
) -> None:
    """Profiler should intercept queries and store SQL and duration."""
    with engine.connect() as conn:
        conn.execute(text(sql_query))

    assert len(queries) == 1
    assert sql_query in str(queries[0]["sql"])
    assert "duration" in queries[0]
