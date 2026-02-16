import time
from sqlalchemy import event
from sqlalchemy.engine import Engine
from .storage import request_queries


def setup_sql_profiler(engine: Engine):

    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault("query_start_time", []).append(time.time())

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total = time.time() - conn.info["query_start_time"].pop(-1)

        queries = request_queries.get()
        queries.append({
            "sql": statement,
            "params": parameters,
            "duration": round(total, 5),
        })
        request_queries.set(queries)
