from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import test_connection

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