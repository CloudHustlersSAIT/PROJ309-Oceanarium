# Oceanarium Backend

FastAPI backend for the Oceanarium Tour Scheduling system.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

## Quick Start (Docker)

```bash
cd backend

# Start PostgreSQL + Backend (builds image on first run)
docker compose up -d

# Verify it's running
curl http://localhost:8000/health
# → {"status":"ok"}
```

The API is now available at:
- **API:** http://localhost:8000
- **Swagger Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## Docker Commands

```bash
# Start all services
docker compose up -d

# View logs (follow mode)
docker compose logs -f backend

# Stop all services
docker compose down

# Stop and remove volumes (wipes database)
docker compose down -v

# Rebuild after code changes
docker compose up -d --build
```

## Running Tests

Tests use an in-memory SQLite database — no Docker or PostgreSQL needed:

```bash
cd backend

# Run all tests
python3 -m pytest tests/ -v

# Run with coverage report
python3 -m pytest tests/ -v --cov=app --cov-report=term-missing

# Run specific test categories
python3 -m pytest tests/unit/ -v          # Unit tests only
python3 -m pytest tests/api/ -v           # API tests only
python3 -m pytest tests/integration/ -v   # Integration tests only
```

## Database Migrations

Migrations run automatically when the Docker container starts. To run them manually:

```bash
# Apply all pending migrations
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/oceanarium \
  python3 -m alembic upgrade head

# Create a new migration after model changes
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/oceanarium \
  python3 -m alembic revision --autogenerate -m "description of changes"
```

## API Endpoints

| Method  | Endpoint                         | Description             |
|---------|----------------------------------|-------------------------|
| GET     | /health                          | Health check            |
| GET     | /health/db                       | Database health check   |
| GET     | /guides                          | List all guides         |
| POST    | /guides                          | Create guide            |
| GET     | /guides/{id}                     | Get guide details       |
| PATCH   | /guides/{id}                     | Update guide            |
| PUT     | /guides/{id}/availability        | Set guide availability  |
| GET     | /tours                           | List all tours          |
| GET     | /tours/unassigned                | List unassigned tours   |
| GET     | /tours/{id}                      | Get tour details        |
| POST    | /tours/{id}/assign               | Assign guide to tour    |
| POST    | /tours/{id}/reassign             | Reassign guide to tour  |
| GET     | /tours/{id}/assignment-log       | Assignment history      |
| GET     | /bookings                        | List all bookings       |
| POST    | /bookings                        | Create booking          |
| PATCH   | /bookings/{id}/reschedule        | Reschedule booking      |
| PATCH   | /bookings/{id}/cancel            | Cancel booking          |
| POST    | /issues                          | Report an issue         |
| GET     | /stats                           | Dashboard statistics    |
| GET     | /notifications                   | Notifications           |
| POST    | /sync/trigger                    | Trigger Clorian sync    |
| GET     | /sync/logs                       | Sync history            |

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app factory
│   ├── db.py                # Database engine & session
│   ├── adapters/            # External service clients
│   ├── jobs/                # Background jobs (scheduler)
│   ├── models/              # SQLAlchemy ORM models
│   ├── routers/             # API route handlers
│   ├── schemas/             # Pydantic request/response models
│   └── services/            # Business logic
├── alembic/                 # Database migrations
├── tests/
│   ├── conftest.py          # Test fixtures
│   ├── api/                 # API endpoint tests
│   ├── integration/         # Integration tests
│   └── unit/                # Unit tests
├── docker-compose.yml       # Local development stack
├── Dockerfile               # Production image
├── requirements.txt         # Python dependencies
├── pytest.ini               # Test configuration
└── .coveragerc              # Coverage settings
```
