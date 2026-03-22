import re
import time
from typing import Any

from sqlalchemy import Connection, ExecutionContext, event
from sqlalchemy.engine import Engine

from fastapi_silk.storage import request_queries

_TABLE_PATTERN = re.compile(
    r"\b(?:from|join|update|into|delete\s+from|truncate\s+table|alter\s+table)\s+([\w\"`\.]+)",
    flags=re.IGNORECASE,
)


def _normalize_identifier(identifier: str) -> str:
    cleaned = identifier.strip().strip(";")
    parts = [p.strip().strip('"`[]') for p in cleaned.split(".") if p.strip()]
    return ".".join(parts)


def _extract_table_refs(statement: str) -> list[dict[str, str | None]]:
    refs: list[dict[str, str | None]] = []
    for match in _TABLE_PATTERN.finditer(statement):
        normalized = _normalize_identifier(match.group(1))
        if not normalized:
            continue

        if "." in normalized:
            schema, table = normalized.rsplit(".", 1)
        else:
            schema, table = None, normalized

        refs.append({"schema": schema, "table": table})
    return refs


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
                "database": conn.engine.url.database,
                "table_refs": _extract_table_refs(statement),
            }
        )
        request_queries.set(queries)
