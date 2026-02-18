from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine


def test_profiler_captures_query(
    engine: Engine,
    sql_query: str,
    queries: list[dict[str, Any]],
) -> None:
    """Profiler should intercept queries and store SQL and duration."""
    with engine.connect() as conn:
        conn.execute(text(sql_query))

    assert len(queries) == 1

    captured = queries[0]
    assert sql_query in str(captured["sql"])
    assert "duration" in captured
