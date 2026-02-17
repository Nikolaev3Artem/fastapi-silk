import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from .storage import request_queries


class SQLDebugMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:

        request_queries.set([])

        start = time.time()
        response = await call_next(request)
        total_time = time.time() - start

        queries = request_queries.get()
        db_time = sum(q["duration"] for q in queries)

        response.headers["X-DB-Queries"] = str(len(queries))
        response.headers["X-DB-Time"] = f"{db_time:.4f}s"
        response.headers["X-Total-Time"] = f"{total_time:.4f}s"

        slow = [q for q in queries if q["duration"] > 0.1]

        if slow:
            print("\n🐢 Slow queries detected:")
            for q in slow:
                print(f"{q['duration']}s → {q['sql']}\n")

            print(f"Request duration: {db_time:.4f}s\n")

        return response
