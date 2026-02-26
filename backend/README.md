# Oceanarium Backend

FastAPI backend for the Oceanarium Tour Scheduling system.

## Prerequisites

- Python 3.12
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

## Quick Start — Local Backend + Docker DB (recommended)

Run only PostgreSQL in Docker and the FastAPI backend directly on your machine. This gives you faster restarts and native debugger support.

```bash
cd backend

# 1. Start PostgreSQL only
docker compose up -d db

# 2. Install Python dependencies
python3 -m pip install -r requirements.txt

# 3. Run database migrations
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/oceanarium \
  python3 -m alembic upgrade head

# 4. Start the backend with hot-reload
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/oceanarium \
  python3 -m uvicorn app.main:app --reload --port 8000
```

The API is now available at:
- **API:** http://localhost:8000
- **Swagger Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## Quick Start — Full Docker Stack

Run both PostgreSQL and the backend in Docker containers:

```bash
cd backend

# Start PostgreSQL + Backend (builds image on first run)
docker compose --profile full up -d

# Verify it's running
curl http://localhost:8000/health
# → {"status":"ok"}
```

## Docker Commands

```bash
# Start PostgreSQL only (for local backend development)
docker compose up -d db

# Start full stack (DB + backend in Docker)
docker compose --profile full up -d

# View logs (follow mode)
docker compose --profile full logs -f backend

# Stop all services
docker compose down

# Stop and remove volumes (wipes database)
docker compose down -v

# Rebuild backend image after dependency changes
docker compose --profile full up -d --build
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

## Git Hooks (pre-push)

A pre-push hook runs the full Backend CI checks (pytest + 95% coverage) before every push that includes `backend/` changes.

### Setup (once per clone)

```bash
# 1. Create a local venv (if you don't have one yet)
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Install the hook
cd ..
bash scripts/install-hooks.sh
```

After this, every `git push` with backend changes will automatically run the test suite. The push is blocked if tests fail or coverage drops below 95%.

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
| GET     | /health                          | Health + DB status      |
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
| GET     | /bookings/unassigned             | Bookings without guide  |
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
