import time
from typing import Any
from sqlalchemy import Connection, ExecutionContext, event
from sqlalchemy.engine import Engine
from .storage import request_queries


def setup_sql_profiler(engine: Engine) -> None:

    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(
        conn: Connection,
        cursor: Any,
        statement: str,
        parameters: dict[str, Any] | tuple[Any, ...] | list[tuple[Any, ...]],
        context: ExecutionContext | None,
        executemany: bool,
    ) -> None:
        conn.info.setdefault("query_start_time", []).append(time.time())

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(
        conn: Connection,
        cursor: Any,
        statement: str,
        parameters: dict[str, Any] | tuple[Any, ...] | list[tuple[Any, ...]],
        context: ExecutionContext | None,
        executemany: bool,
    ) -> None:
        total = time.time() - conn.info["query_start_time"].pop(-1)

        queries = request_queries.get()
        queries.append(
            {
                "sql": statement,
                "params": parameters,
                "duration": round(total, 5),
            }
        )
        request_queries.set(queries)
