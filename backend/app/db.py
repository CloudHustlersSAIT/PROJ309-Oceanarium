"""
Database engine configuration and connection helpers.

Reads DATABASE_URL from environment variables, creates a SQLAlchemy engine,
and exposes ``get_db()`` for FastAPI dependency injection plus a
``test_connection()`` health-check helper.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment variables")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Yield a raw SQLAlchemy connection for use in FastAPI ``Depends()``.

    The connection is automatically closed when the request finishes.
    Routes receive this connection and pass it to service functions so that
    services never need to import ``engine`` directly.

    Yields:
        sqlalchemy.engine.Connection: An open database connection.
    """
    with engine.connect() as conn:
        yield conn


def test_connection():
    """Run ``SELECT 1`` to verify the database is reachable.

    Returns:
        int | None: ``1`` on success, ``None`` if the connection fails.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            value = result.scalar_one()
            print("Database connection successful:", value)
            return value
    except Exception as e:
        print("Database connection failed:", e)
        return None
