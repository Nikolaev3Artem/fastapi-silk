import contextvars

request_queries = contextvars.ContextVar(
    "request_queries",
    default=[]
)
