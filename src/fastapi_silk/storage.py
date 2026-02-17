import contextvars
from typing import Any

request_queries: contextvars.ContextVar[list[Any]] = contextvars.ContextVar(
    "request_queries", default=[]
)
