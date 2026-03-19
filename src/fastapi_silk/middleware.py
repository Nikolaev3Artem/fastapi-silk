import time
from collections import Counter

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from fastapi_silk.storage import request_queries, recent_queries


class SQLDebugMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip logging for Silk UI internal requests and browser metadata requests
        path = str(request.url.path)
        if path.startswith("/_silk") or path.startswith("/.well-known"):
            return await call_next(request)

        request_queries.set([])

        start = time.time()
        response = await call_next(request)
        total_time = time.time() - start

        queries = request_queries.get()
        db_time = sum(q["duration"] for q in queries)

        database_hits: Counter[str] = Counter()
        schema_hits: Counter[str] = Counter()
        table_hits: Counter[str] = Counter()

        for query in queries:
            db_name = str(query.get("database") or "default")
            database_hits[db_name] += 1

            for ref in query.get("table_refs", []):
                table_name = ref.get("table")
                if not table_name:
                    continue

                schema_name = ref.get("schema")
                if schema_name:
                    schema_hits[str(schema_name)] += 1
                    table_key = f"{schema_name}.{table_name}"
                else:
                    table_key = str(table_name)

                table_hits[table_key] += 1

        response.headers["X-DB-Queries"] = str(len(queries))
        response.headers["X-DB-Time"] = f"{db_time:.4f}s"
        response.headers["X-Total-Time"] = f"{total_time:.4f}s"

        slow = [q for q in queries if q["duration"] > 0.1]

        if slow:
            print("\n🐢 Slow queries detected:")
            for q in slow:
                print(f"{q['duration']}s → {q['sql']}\n")

            print(f"Request duration: {db_time:.4f}s\n")

        # Store a summary in the shared recent buffer so a UI route can show it
        try:
            recent_queries.append(
                {
                    "time": time.time(),
                    "path": str(request.url.path),
                    "method": request.method,
                    "queries": queries,
                    "db_time": round(db_time, 5),
                    "total_time": round(total_time, 5),
                    "database_hits": dict(database_hits),
                    "schema_hits": dict(schema_hits),
                    "table_hits": dict(table_hits),
                    "database_trigger_count": sum(database_hits.values()),
                    "schema_trigger_count": sum(schema_hits.values()),
                    "table_trigger_count": sum(table_hits.values()),
                }
            )
        except Exception:
            # be defensive: don't break request handling for UI errors
            pass
        return response
