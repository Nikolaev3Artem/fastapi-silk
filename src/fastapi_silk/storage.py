import contextvars
from typing import Any
from collections import deque

# Per-request ContextVar that the profiler writes into
request_queries: contextvars.ContextVar[list[Any]] = contextvars.ContextVar(
    "request_queries", default=[]
)

# In-memory buffer of recent request summaries (shared across requests).
# Each entry is a dict with keys: time, path, method, queries, db_time, total_time
recent_queries: deque[dict[str, Any]] = deque(maxlen=200)
