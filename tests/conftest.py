from collections.abc import Iterator
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from fastapi_silk.profiler import setup_sql_profiler
from fastapi_silk.storage import request_queries
from tests.fixtures.sql_queries import SQL_QUERIES


@pytest.fixture
def engine() -> Engine:
    """Create an in-memory SQLite engine with SQL profiler attached."""
    db_engine = create_engine("sqlite:///:memory:")
    setup_sql_profiler(db_engine)
    return db_engine


@pytest.fixture(autouse=True)
def reset_queries() -> Iterator[None]:
    """Ensure query storage is clean before and after each test."""
    request_queries.set([])
    try:
        yield
    finally:
        request_queries.set([])


@pytest.fixture(params=SQL_QUERIES)
def sql_query(request: pytest.FixtureRequest) -> str:
    """SQL statements to execute, easily extendable/parameterized."""
    return str(request.param)


@pytest.fixture
def queries() -> list[dict[str, Any]]:
    """Expose captured SQL queries for assertions."""
    return request_queries.get()
