import sys
import os

from sqlalchemy import create_engine, text

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from fastapi_silk.profiler import setup_sql_profiler
from fastapi_silk.storage import request_queries


def test_profiler_captures_query():
    """Test that the profiler intercepts queries and stores them."""
    # 1. Setup Engine
    engine = create_engine("sqlite:///:memory:")
    setup_sql_profiler(engine)

    # 2. Reset storage (just in case default list is dirty)
    request_queries.set([])

    # 3. Execute a query
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    # 4. Verify capture
    queries = request_queries.get()
    assert len(queries) == 1
    assert "SELECT 1" in str(queries[0]["sql"])
    assert "duration" in queries[0]
