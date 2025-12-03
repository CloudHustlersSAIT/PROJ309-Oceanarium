from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
from .db import test_connection, engine

app = FastAPI(title="My Project API")

# Allow Vue dev server to talk to FastAPI
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    try:
        value = test_connection()
        return {"status": "ok", "db_check": value}
    except Exception as e:
        # In production you’d log the error instead
        return {"status": "error", "detail": str(e)}

#example endpoint that queries the group_members table
@app.get("/group_members_example")
def read_group_members():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM group_members"))
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
        return rows
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    
@app.get("/guides")
def read_guides():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM guides"))
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
        return rows
    except Exception as e:
        return {"status": "error", "detail": str(e)}