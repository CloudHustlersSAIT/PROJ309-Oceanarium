# Oceanarium Backend

FastAPI backend for the Oceanarium Tour Scheduling system.

## Prerequisites

- Python 3.9+
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

## Quick Start — Local Backend + Docker DB (recommended)

Run only PostgreSQL in Docker and the FastAPI backend directly on your machine. This gives you faster restarts and native debugger support.

```bash
cd backend

# 1. Start PostgreSQL only
docker compose up -d db

# 2. Create and activate a virtual environment (once per clone)
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Run database migrations
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/oceanarium \
  python3 -m alembic upgrade head

# 5. Start the backend with hot-reload
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/oceanarium \
  uvicorn app.main:app --reload --port 8000
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

## Reset Database

A helper script wipes the database volume and re-runs all Alembic migrations:

```bash
cd backend/scripts
bash reset-db.sh

# Optionally seed data via the sync endpoint (backend must be running)
bash reset-db.sh --seed
```

## Running Tests

Tests run against PostgreSQL (same engine as production). Start the database first:

```bash
cd backend

# 1. Start PostgreSQL (if not already running)
docker compose up -d db

# 2. Create the test database (one-time)
docker compose exec db psql -U postgres -c "CREATE DATABASE oceanarium_test"

# 3. Run all tests
python3 -m pytest tests/ -v

# Run with coverage report
python3 -m pytest tests/ -v --cov=app --cov-report=term-missing

# Run specific test categories
python3 -m pytest tests/unit/ -v          # Unit tests only
python3 -m pytest tests/api/ -v           # API tests only
python3 -m pytest tests/integration/ -v   # Integration tests only
```

## Git Hooks (pre-push)

A pre-push hook runs the full Backend CI checks (pytest + 95% coverage) before every push that includes `backend/` changes. It automatically starts the Docker DB and creates the test database if needed.

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

Full interactive docs are available at http://localhost:8000/docs once the server is running.

| Method | Endpoint                      | Description                 |
| ------ | ----------------------------- | --------------------------- |
| GET    | /health                       | Health + DB status          |
| GET    | /guides                       | List all guides             |
| POST   | /guides                       | Create guide                |
| GET    | /guides/{id}                  | Get guide details           |
| PATCH  | /guides/{id}                  | Update guide                |
| PUT    | /guides/{id}/availability     | Set guide availability      |
| GET    | /tours                        | List all tours              |
| POST   | /tours                        | Create tour                 |
| GET    | /tours/{id}                   | Get tour details            |
| PATCH  | /tours/{id}                   | Update tour                 |
| DELETE | /tours/{id}                   | Delete tour                 |
| GET    | /bookings                     | List all bookings           |
| GET    | /bookings/unassigned          | Bookings without guide      |
| POST   | /bookings                     | Create booking              |
| PATCH  | /bookings/{id}/reschedule     | Reschedule booking          |
| PATCH  | /bookings/{id}/cancel         | Cancel booking              |
| POST   | /bookings/{id}/assign         | Assign guide to booking     |
| POST   | /bookings/{id}/reassign       | Reassign guide to booking   |
| POST   | /bookings/auto-assign         | Auto-assign guides          |
| GET    | /bookings/{id}/assignment-log | Assignment history          |
| GET    | /schedules                    | List schedules              |
| POST   | /schedules                    | Create schedule             |
| GET    | /schedules/{id}               | Get schedule details        |
| PATCH  | /schedules/{id}               | Update schedule             |
| DELETE | /schedules/{id}               | Delete schedule             |
| GET    | /customers                    | List all customers          |
| POST   | /customers                    | Create customer             |
| GET    | /customers/{id}               | Get customer details        |
| PATCH  | /customers/{id}               | Update customer             |
| DELETE | /customers/{id}               | Delete customer             |
| GET    | /resources                    | List all resources          |
| POST   | /resources                    | Create resource             |
| GET    | /resources/{id}               | Get resource details        |
| PATCH  | /resources/{id}               | Update resource             |
| DELETE | /resources/{id}               | Delete resource             |
| GET    | /costs                        | List costs (filter by tour) |
| POST   | /costs                        | Create cost                 |
| GET    | /costs/{id}                   | Get cost details            |
| PATCH  | /costs/{id}                   | Update cost                 |
| DELETE | /costs/{id}                   | Delete cost                 |
| GET    | /surveys                      | List all surveys            |
| POST   | /surveys                      | Create survey               |
| GET    | /surveys/{id}                 | Get survey details          |
| PATCH  | /surveys/{id}                 | Update survey               |
| DELETE | /surveys/{id}                 | Delete survey               |
| GET    | /users                        | List all users              |
| POST   | /users                        | Create user                 |
| GET    | /users/{id}                   | Get user details            |
| PATCH  | /users/{id}                   | Update user                 |
| DELETE | /users/{id}                   | Delete user                 |
| POST   | /issues                       | Report an issue             |
| GET    | /stats                        | Dashboard statistics        |
| GET    | /notifications                | Notifications               |
| POST   | /sync/trigger                 | Trigger Clorian sync        |
| GET    | /sync/logs                    | Sync history                |

## Docs & Tools

- **ERD:** `docs/database-erd.md` — entity-relationship diagram in Mermaid format
- **Insomnia:** `docs/insomnia.json` — importable API collection for [Insomnia](https://insomnia.rest/)

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
├── docs/
│   ├── database-erd.md      # ERD (Mermaid)
│   └── insomnia.json        # Insomnia API collection
├── scripts/
│   └── reset-db.sh          # Wipe DB + re-run migrations
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
