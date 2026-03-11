import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://oceanarium:oceanarium@localhost:5432/oceanarium_test")
os.environ.setdefault("ENV", "development")

from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.db import get_db
from app.main import app


def _mock_get_db():
    conn = MagicMock()
    yield conn


app.dependency_overrides[get_db] = _mock_get_db


@pytest.fixture()
def mock_conn():
    return MagicMock()


@pytest.fixture()
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
