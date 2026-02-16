# FastAPI-Silk

## About the Project

**FastAPI-Silk** is a profiling and monitoring tool for **FastAPI**, inspired by [django-silk](https://github.com/jazzband/django-silk).  
It helps track request performance, SQL queries, and provides insights to optimize your FastAPI application.

## Dependencies

- Python 3.10+
- FastAPI
- SQLAlchemy (optional, for SQL query profiling)
- Uvicorn or any ASGI server

## Installation

You can install FastAPI-Silk via pip:

```bash
pip install fastapi-silk
```

In main.py of your project:

```bash
from fastapi_silk import SQLDebugMiddleware
```

```bash
app.add_middleware(SQLDebugMiddleware)
```

At the database engine file:

```bash
setup_sql_profiler(your_engine)
```

After setup you will see all timmings and requests to the database all time you trigger your endpoints
