# Oceanarium Backend

FastAPI backend for the Oceanarium management system.

## Quick Start

```bash
cd backend
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

Create a `.env` file in this folder:

```bash
DATABASE_URL=postgresql+psycopg2://USER:PASS@HOST/DBNAME
```

Run the server:

```bash
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Interactive docs (Swagger): http://127.0.0.1:8000/docs
- Alternative docs (ReDoc): http://127.0.0.1:8000/redoc

## Database Setup

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose

### Start PostgreSQL

```bash
docker compose up db -d
```

This starts a PostgreSQL 16 container on port 5432 with credentials `oceanarium:oceanarium`.

### Run Migrations

```bash
cd backend
alembic upgrade head
```

### Rollback

```bash
alembic downgrade -1     # rollback one migration
alembic downgrade base   # rollback everything
```

### Create a New Migration

```bash
alembic revision -m "description of change"
```

Then edit the generated file in `migrations/versions/` adding `op.execute()` calls with raw SQL.

### Verify Tables

```bash
docker compose exec db psql -U oceanarium -c "\dt"
```

### Destroy and Rebuild

```bash
docker compose down -v   # removes containers and pgdata volume
docker compose up db -d
cd backend && alembic upgrade head
```

## Architecture Overview

The backend follows a **layered domain architecture** (see [ADR-002](docs/ADR/ADR-002-layered-domain-architecture.md)). We are currently on **Phase 1** of 6 — routes and services are extracted, but raw SQL still lives in services temporarily.

### Request Flow

```
HTTP Request
    |
    v
  Route  (thin handler — parses request, calls service, returns response)
    |
    v
 Service  (business logic, validation, raw SQL for now)
    |
    v
 Database  (PostgreSQL via SQLAlchemy engine)
```

### Folder Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # App factory: FastAPI instance, CORS, router registration
│   ├── db.py                # Database engine, connection helper (get_db), health check
│   │
│   ├── routes/              # HTTP layer — thin handlers, no business logic
│   │   ├── __init__.py
│   │   ├── health.py        # GET /health, GET /health/db
│   │   ├── reservation.py   # GET/POST /reservations, PATCH reschedule/cancel (+ deprecated /bookings aliases)
│   │   ├── guide.py         # GET /guides
│   │   ├── tour.py          # GET /tours
│   │   ├── schedule.py      # GET /schedules
│   │   ├── notification.py  # GET /notifications
│   │   ├── issue.py         # POST /issues
│   │   ├── stats.py         # GET /stats
│   │   └── mock.py          # POST /mock/run
│   │
│   └── services/            # Business logic, validation, orchestration
│       ├── __init__.py
│       ├── exceptions.py    # Domain exceptions (NotFoundError, ConflictError, etc.)
│       ├── reservation.py   # Reservation CRUD + conflict detection
│       ├── guide.py         # Guide queries
│       ├── tour.py          # Tour queries
│       ├── schedule.py      # Schedule queries + filters
│       ├── notification.py  # Notification queries
│       ├── issue.py         # Issue creation
│       ├── stats.py         # Dashboard aggregation
│       └── mock_poller.py   # Mock Clorian data generation + staging
│
├── migrations/              # Alembic raw SQL migrations
│   ├── env.py               # Loads DATABASE_URL from environment
│   ├── script.py.mako       # Template for new revisions
│   └── versions/
│       └── 0001_initial_schema.py  # 20-table initial schema
│
├── docs/                    # Architecture decisions, domain docs, ERD
├── alembic.ini              # Alembic configuration (URL loaded from env)
├── Dockerfile
├── requirements.txt
└── .env                     # Not committed — see .gitignore
```

### Layer Rules

These are the rules every developer must follow when writing code:

| Rule | Details |
|------|---------|
| **Routes are thin** | Parse the request, call a service function, return the response. No business logic, no SQL. |
| **Services own the logic** | Validation, conflict detection, orchestration. They receive a `conn` parameter — they never import `engine`. |
| **Services raise domain exceptions** | `NotFoundError`, `ConflictError`, `ValidationError` from `services/exceptions.py`. Never `HTTPException`. |
| **Routes catch domain exceptions** | Map them to HTTP status codes: `NotFoundError` -> 404, `ConflictError` -> 409, `ValidationError` -> 400. |
| **DB connections via dependency injection** | Most routes get a connection with `conn = Depends(get_db)` and pass it to service functions. |
| **Pydantic schemas live in route files** | Temporary — Phase 3 will extract them to a `schemas/` folder. |
| **Raw SQL is temporary** | Phase 2 will introduce SQLAlchemy ORM models and a `repositories/` layer. |

### Dependency Direction

```
routes --> services --> (database via conn parameter)
```

No layer may import from a layer above it. Services never import from routes.

## API Reference

The API currently exposes canonical reservation endpoints under `/reservations`.
Legacy `/bookings` endpoints are still available as deprecated aliases for backward compatibility.

| Method | Path | Route File | Description |
|--------|------|------------|-------------|
| GET | `/health` | `routes/health.py` | App liveness check |
| GET | `/health/db` | `routes/health.py` | Database connectivity check |
| GET | `/reservations` | `routes/reservation.py` | List all reservations (newest first) |
| POST | `/reservations` | `routes/reservation.py` | Create a reservation |
| PATCH | `/reservations/{id}/reschedule` | `routes/reservation.py` | Reschedule a reservation |
| PATCH | `/reservations/{id}/cancel` | `routes/reservation.py` | Cancel a reservation |
| GET | `/bookings` | `routes/reservation.py` | Deprecated alias of `GET /reservations` |
| POST | `/bookings` | `routes/reservation.py` | Deprecated alias of `POST /reservations` |
| PATCH | `/bookings/{id}/reschedule` | `routes/reservation.py` | Deprecated alias of `/reservations/{id}/reschedule` |
| PATCH | `/bookings/{id}/cancel` | `routes/reservation.py` | Deprecated alias of `/reservations/{id}/cancel` |
| GET | `/guides` | `routes/guide.py` | List all guides |
| GET | `/tours` | `routes/tour.py` | List all tours |
| GET | `/schedules` | `routes/schedule.py` | List calendar events from schedule table (optional: `start_date`, `end_date`, `status`) |
| GET | `/notifications` | `routes/notification.py` | List recent notifications (last 10) |
| POST | `/issues` | `routes/issue.py` | Report a new issue |
| GET | `/stats` | `routes/stats.py` | Dashboard stats for today |
| POST | `/mock/run` | `routes/mock.py` | Generate and stage deterministic mock Clorian reservation payloads |

### Schedules Endpoint Notes

- `GET /schedules` supports optional filters:
    - `start_date=YYYY-MM-DD` (events ending on/after date)
    - `end_date=YYYY-MM-DD` (events starting before next day of date)
    - `status` (case-insensitive exact match)
- Validation rule:
    - Returns `400` when `start_date > end_date`
- Response includes joined and aggregated fields:
    - `tour_name`, `guide_name`, `reservation_count`

### Mock Poller Endpoint Notes

- `POST /mock/run` request body (`MockRunRequest`):
    - `seed` (default `42`)
    - `batch_size` (default `10`, min `1`, max `500`)
    - `update_ratio` (default `0.30`)
    - `unchanged_ratio` (default `0.20`)
- Validation rules:
    - `update_ratio + unchanged_ratio <= 1.0`
    - At least one row in `public.tours` must exist
- Behavior:
    - Creates a `poll_execution` run row
    - Generates deterministic reservation payloads with nested tickets
    - Writes JSON payloads to `public.poll_staging`
    - Finalizes run as `SUCCESS` or `FAILED`
- Returns summary counts:
    - `generated_total`, `generated_created`, `generated_updated`, `generated_unchanged`

Frontend integration note:
- Schedule endpoint quick guide: `docs/SCHEDULE_ENDPOINT_FRONTEND_GUIDE.md`

## How to Add a New Endpoint

Follow this checklist when adding a new feature:

### 1. Create the service (`app/services/your_feature.py`)

```python
from sqlalchemy import text
from .exceptions import NotFoundError

def get_something(conn, item_id: int):
    """Fetch a single item by ID. Raises NotFoundError if missing."""
    row = conn.execute(
        text("SELECT * FROM items WHERE id = :id"),
        {"id": item_id},
    ).fetchone()

    if not row:
        raise NotFoundError(f"Item {item_id} not found")

    columns = row.keys()
    return dict(zip(columns, row))
```

Key points:
- `conn` is always the first parameter (injected by the route via `Depends(get_db)`)
- Raise domain exceptions, not `HTTPException`
- Call `conn.commit()` after INSERT/UPDATE/DELETE

### 2. Create the route (`app/routes/your_feature.py`)

```python
from fastapi import APIRouter, Depends, HTTPException

from ..db import get_db
from ..services import your_feature as your_feature_service
from ..services.exceptions import NotFoundError

router = APIRouter(prefix="/your-feature", tags=["Your Feature"])

@router.get("/{item_id}")
def get_item(item_id: int, conn=Depends(get_db)):
    """Fetch a single item by ID."""
    try:
        return your_feature_service.get_something(conn, item_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
```

### 3. Register the router (`app/main.py`)

```python
from .routes.your_feature import router as your_feature_router

app.include_router(your_feature_router)
```

### 4. Test it

```bash
uvicorn app.main:app --reload
# Then visit http://127.0.0.1:8000/docs to test via Swagger
```

## Domain Exceptions

Defined in `app/services/exceptions.py`:

| Exception | HTTP Status | When to Use |
|-----------|-------------|-------------|
| `DomainError` | (base class) | Don't raise directly — use a specific subclass |
| `ValidationError` | 400 | Invalid input (negative tickets, bad ratios, etc.) |
| `NotFoundError` | 404 | Record not found in the database |
| `ConflictError` | 409 | Business rule conflict (e.g., overlapping bookings) |

Usage in a service:

```python
from .exceptions import ValidationError, NotFoundError

def my_function(conn, data):
    if data.amount < 0:
        raise ValidationError("Amount cannot be negative")
```

The route layer catches these and converts them to `HTTPException` with the correct status code.

## Docker

The project uses Docker Compose (defined at the repo root) to run PostgreSQL and the backend together:

```bash
docker compose up -d          # start both db and backend
docker compose up db -d       # start only PostgreSQL
docker compose down           # stop all services
docker compose down -v        # stop and destroy volumes (full reset)
```

To build and run the backend image standalone:

```bash
docker build -t oceanarium-backend .
docker run -p 8000:8000 --env-file .env oceanarium-backend
```

The Dockerfile uses `app.main:app` as the uvicorn entrypoint — this must remain a module-level `FastAPI()` instance in `main.py`.

## CI/CD

Two GitHub Actions workflows automate migration validation and production deployment.

### CI — Validate Migrations (`.github/workflows/ci.yml`)

Runs on every **pull request** that touches `backend/**`.

1. Spins up a disposable PostgreSQL 16 service container.
2. Installs Python 3.11 and project dependencies.
3. Executes `alembic upgrade head` → `alembic downgrade base` → `alembic upgrade head` to prove migrations are reversible and idempotent.

A failing migration blocks the PR from merging.

### CD — Migrate & Deploy (`.github/workflows/cd.yml`)

Runs on every **push to `main`** that touches `backend/**`.

1. Opens SSH access to the EC2 security group.
2. SSHs into the EC2 instance, pulls the latest code, installs dependencies, runs `alembic upgrade head` against the production RDS database, and restarts the service. Migrations run **before** the service restarts so the schema is always ahead of the code.
3. Closes SSH access in the security group (runs even if deploy fails).

The EC2 instance connects to RDS over the private VPC network — no public database access is needed.

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | IAM access key for EC2 security group management |
| `AWS_SECRET_ACCESS_KEY` | IAM secret key |
| `AWS_REGION` | AWS region (e.g. `us-east-2`) |
| `AWS_SG_ID` | EC2 security group ID (for temporary SSH access) |
| `EC2_HOST` | EC2 instance public IP or hostname |
| `EC2_USERNAME` | SSH username on the EC2 instance |
| `EC2_SSH_KEY` | Private SSH key for the EC2 instance |

## Key Documentation

| Document | Path | Description |
|----------|------|-------------|
| ADR-001 | `docs/ADR/ADR-001-drop-reservation-table.md` | Why we dropped the reservation table |
| ADR-002 | `docs/ADR/ADR-002-layered-domain-architecture.md` | Layered architecture decision (this structure) |
| DDD-001 | `docs/DDD/DDD-001-domain-model-overview.md` | Domain model and bounded contexts |
| ERD | `docs/db/ERD.md` | Entity-relationship diagram (20+ tables) |
| FDR-001 | `docs/FDR/FDR-001-booking-ingestion-from-clorian.md` | How bookings come from Clorian |
| FDR-002 | `docs/FDR/FDR-002-guide-assignment-rules.md` | Guide assignment algorithm |
| FDR-003 | `docs/FDR/FDR-003-notifications.md` | Notification system design |
| FDR-004 | `docs/FDR/FDR-004-auto-rescheduling.md` | Auto-rescheduling logic |

## Architecture Roadmap (ADR-002 Phases)

| Phase | Status | What It Adds |
|-------|--------|-------------|
| 1 | **Done** | `routes/` + `services/` extraction (current state) |
| 2 | Planned | SQLAlchemy ORM `models/` + `repositories/` (ADR-003) |
| 3 | Planned | Pydantic `schemas/` extraction from routes |
| 4 | Planned | `infrastructure/` + `config.py` centralization |
| 5 | **Done** | Alembic `migrations/` — raw SQL, 20 tables |
| 6 | Planned | Clorian `adapters/` integration (ADR-005) |
