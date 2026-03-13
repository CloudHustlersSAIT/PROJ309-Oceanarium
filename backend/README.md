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
FIREBASE_SERVICE_ACCOUNT_JSON={...}
# Optional local-only auth bypass:
# ENV=development
# AUTH_BYPASS=true

# Email configuration (for notifications)
EMAIL_ENABLED=true
RESEND_API_KEY=re_your_api_key_here  # Get from https://resend.com/api-keys
EMAIL_FROM=onboarding@resend.dev      # Use this for testing; verify your domain for production
EMAIL_FROM_NAME=Oceanarium Scheduling System
FRONTEND_URL=http://localhost:5173
```

### Email Setup (for Notifications)

1. **Sign up for Resend.com**: https://resend.com
2. **Get your API key**: https://resend.com/api-keys
3. **Add to `.env`**: Set `RESEND_API_KEY` with your API key
4. **Testing**: Use `EMAIL_FROM=onboarding@resend.dev` (Resend's test domain)
5. **Production**: Verify your domain at https://resend.com/domains, then update `EMAIL_FROM` to use your domain (e.g., `notifications@yourdomain.com`)

#### Testing Email Delivery

Once your backend is running, test email delivery using the test endpoint:

```bash
# Test system email
curl -X POST "http://127.0.0.1:8000/notifications/test-email?to_email=YOUR_EMAIL@gmail.com&template_type=system"

# Test guide assignment template
curl -X POST "http://127.0.0.1:8000/notifications/test-email?to_email=YOUR_EMAIL@gmail.com&template_type=guide_assignment"

# Test admin urgent alert template
curl -X POST "http://127.0.0.1:8000/notifications/test-email?to_email=YOUR_EMAIL@gmail.com&template_type=admin_alert"
```

**Check backend logs** to see detailed email sending information:
- `📧 send_email() called - To: ...`
- `🚀 Sending email via Resend API...`
- `✅ Email sent successfully! Resend Email ID: ...`

**Note:** If emails don't appear in your inbox, check:
1. Spam/Junk folder
2. Resend dashboard (https://resend.com/emails) to verify delivery status
3. Backend logs for any errors

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

The backend follows a **layered domain architecture** (see [ADR-002](docs/ADR/ADR-002-layered-domain-architecture.md)). Routes stay thin, services own business logic, and SQL is currently executed in services through injected DB connections.

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
├── .env.example            # Environment template for local setup
├── alembic.ini             # Alembic configuration (URL loaded from env)
├── Dockerfile
├── pyproject.toml          # Ruff, pytest, coverage settings
├── requirements.txt
├── load_tests/             # Locust performance scenarios
├── tests/                  # Backend unit/integration tests
├── app/
│   ├── __init__.py
│   ├── main.py              # App factory: FastAPI instance, CORS, router registration
│   ├── db.py                # Database engine, connection helper (get_db), health check
│   ├── firebase_auth.py     # Firebase Admin initialization + token verification
│   ├── dependencies/
│   │   ├── __init__.py
│   │   └── auth.py          # Bearer token extraction + authenticated user dependency
│   │
│   ├── routes/              # HTTP layer — thin handlers, no business logic
│   │   ├── __init__.py
│   │   ├── auth.py          # GET /auth/me
│   │   ├── customer.py      # GET/POST /customers, PATCH /customers/{customer_id}
│   │   ├── health.py        # GET /health, GET /health/db
│   │   ├── reservation.py   # GET/POST /reservations, PATCH reschedule/cancel (+ deprecated /bookings aliases)
│   │   ├── guide.py         # GET /guides
│   │   ├── guide_requests.py  # GET/POST /guide/swap-* (swap candidates, create, list, accept, reject)
│   │   ├── tour.py          # GET /tours
│   │   ├── schedule.py      # GET /schedules
│   │   ├── notification.py  # GET /notifications
│   │   ├── issue.py         # POST /issues
│   │   ├── stats.py         # GET /stats
│   │   └── mock.py          # POST /mock/run, POST /mock/process
│   │
│   └── services/            # Business logic, validation, orchestration
│       ├── __init__.py
│       ├── exceptions.py    # Domain exceptions (NotFoundError, ConflictError, etc.)
│       ├── error_handlers.py  # Maps domain exceptions to HTTP errors
│       ├── auth.py          # Authenticated user resolution from token claims
│       ├── customer.py      # Customer list/create/update + MANUAL ID generation
│       ├── reservation.py   # Reservation CRUD + conflict detection
│       ├── guide.py         # Guide queries
│       ├── guide_requests.py   # Swap candidates, create/list/accept/reject swap requests
│       ├── guide_assignment.py  # Auto/manual guide assignment logic
│       ├── tour.py          # Tour queries
│       ├── schedule.py      # Schedule queries + filters
│       ├── notification.py  # Notification queries + create helper
│       ├── issue.py         # Issue creation
│       ├── stats.py         # Dashboard aggregation
│       ├── mock_poller.py   # Mock Clorian data generation + staging
│       ├── poller_listener.py  # Staging ingestion + change detection (FDR-004)
│       └── rescheduling.py  # Auto re-scheduling service (FDR-004)
│
├── migrations/              # Alembic raw SQL migrations
│   ├── env.py               # Loads DATABASE_URL from environment
│   ├── script.py.mako       # Template for new revisions
│   └── versions/
│       └── 0001_initial_schema.py  # 20-table initial schema
│
├── docs/                    # Architecture decisions, domain docs, ERD
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
| GET | `/auth/me` | `routes/auth.py` | Resolve current authenticated user profile from Firebase token |
| GET | `/customers` | `routes/customer.py` | List customers with aggregated `total_visits` and `first_tour_date` |
| POST | `/customers` | `routes/customer.py` | Create customer (optional `clorian_client_id`, auto-generates `MANUAL-######` when missing) |
| PATCH | `/customers/{customer_id}` | `routes/customer.py` | Partially update customer by `clorian_client_id` |
| GET | `/reservations` | `routes/reservation.py` | List all reservations (newest first) |
| POST | `/reservations` | `routes/reservation.py` | Create a reservation |
| PATCH | `/reservations/{id}/reschedule` | `routes/reservation.py` | Reschedule a reservation |
| PATCH | `/reservations/{id}/cancel` | `routes/reservation.py` | Cancel a reservation |
| GET | `/bookings` | `routes/reservation.py` | Deprecated alias of `GET /reservations` |
| POST | `/bookings` | `routes/reservation.py` | Deprecated alias of `POST /reservations` |
| PATCH | `/bookings/{id}/reschedule` | `routes/reservation.py` | Deprecated alias of `/reservations/{id}/reschedule` |
| PATCH | `/bookings/{id}/cancel` | `routes/reservation.py` | Deprecated alias of `/reservations/{id}/cancel` |
| GET | `/guides` | `routes/guide.py` | List all guides |
| POST | `/guides` | `routes/guide.py` | Create a guide |
| PATCH | `/guides/{guide_id}` | `routes/guide.py` | Partially update guide by internal `id` |
| GET | `/tours` | `routes/tour.py` | List all tours |
| GET | `/schedules` | `routes/schedule.py` | List calendar events from schedule table (optional: `start_date`, `end_date`, `status`) |
| GET | `/notifications` | `routes/notification.py` | List recent notifications (last 10) |
| GET | `/notifications/{id}` | `routes/notification.py` | Get full notification detail (marks as read) |
| PATCH | `/notifications/{id}/read` | `routes/notification.py` | Mark a notification as read |
| PATCH | `/notifications/read-all` | `routes/notification.py` | Mark all notifications as read for current user |
| GET | `/notifications/summary` | `routes/notification.py` | Get notification counts by priority and type |
| GET | `/notifications/preferences` | `routes/notification.py` | Get user notification channel preferences |
| PUT | `/notifications/preferences` | `routes/notification.py` | Update notification channel preferences per event type |
| POST | `/notifications/retry-failed` | `routes/notification.py` | Retry failed email notifications (admin only) |
| POST | `/notifications/test-email` | `routes/notification.py` | **TEST ENDPOINT:** Send test email (params: `to_email`, `template_type`) |
| POST | `/issues` | `routes/issue.py` | Report a new issue |
| GET | `/stats` | `routes/stats.py` | Dashboard stats for today |
| POST | `/schedules` | `routes/schedule.py` | Create a schedule |
| POST | `/schedules/{id}/assign` | `routes/schedule.py` | Auto-assign a guide to a schedule |
| PUT | `/schedules/{id}/assign` | `routes/schedule.py` | Manually assign a guide (admin override) |
| DELETE | `/schedules/{id}/guide` | `routes/schedule.py` | Remove guide from schedule and auto-replace (FDR-004 FR-5) |
| POST | `/mock/run` | `routes/mock.py` | Generate and stage deterministic mock Clorian reservation payloads |
| POST | `/mock/process` | `routes/mock.py` | Process staging rows: ingest, detect changes, trigger re-scheduling (FDR-004) |

### Authentication Notes

- `Authorization: Bearer <firebase_id_token>` is required for:
    - `GET /auth/me`
    - `POST /customers`
    - `PATCH /customers/{customer_id}`
    - `POST /guides`
    - `PATCH /guides/{guide_id}`
    - `POST /reservations`
    - `PATCH /reservations/{id}/reschedule`
    - `PATCH /reservations/{id}/cancel`
    - `POST /issues`
- Local bypass exists only when both `ENV=development` and `AUTH_BYPASS=true` are set.
- In local bypass mode, when token verification fails, backend falls back to bypass claims instead of returning `401`.
- Optional local bypass claim overrides:
    - `AUTH_BYPASS_EMAIL` (default: `local-dev@oceanarium.local`)
    - `AUTH_BYPASS_UID` (default: `local-dev-user`)

### Customers Endpoint Notes

- `GET /customers` returns `clorian_client_id`, `full_name`, `email`, `total_visits`, and `first_tour_date`.
- `POST /customers` requires `first_name`, `last_name`, and `email`.
- When `clorian_client_id` is omitted on create, backend generates the next available `MANUAL-######` value (starting at `MANUAL-000001`).
- `PATCH /customers/{customer_id}` supports partial updates of `first_name`, `last_name`, and `email`.

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
    - On successful completion, finalizes run as `SUCCESS`
    - In some error scenarios, the run may not be persisted with a `FAILED` status (e.g., failures inside the transaction can roll back the initial `poll_execution` insert)
- Returns summary counts:
    - `generated_total`, `generated_created`, `generated_updated`, `generated_unchanged`

### Guide Swap Endpoints

All guide swap endpoints live under `/guide` and are implemented in `routes/guide_requests.py` and `services/guide_requests.py`. Swap requests are stored in `tour_assignment_logs` with `assignment_type = 'SWAP'` and `action` values: `SWAP_REQUEST`, `SWAP_ACCEPTED`, `SWAP_REJECTED`.

| Endpoint | Query params | Description |
|----------|--------------|-------------|
| `GET /guide/swap-candidates` | `schedule_id` (required) | Returns active guides who are not the current assignee and have no overlapping ASSIGNED/CONFIRMED schedule. Ordered by `guide_rating` DESC. |
| `POST /guide/swap-request` | `schedule_id`, `guide_id` (both required) | Creates a swap request; `guide_id` is the **requesting** guide. Inserts a row into `tour_assignment_logs` with `action = 'SWAP_REQUEST'`. Returns `{"swap_request_id": id}`. |
| `GET /guide/swap-requests` | `guide_id` (required) | Returns swap requests that **require action from** the given guide (i.e. where that guide is currently assigned to the schedule). Response includes `swap_request_id`, `schedule_id`, `tour_name`, event times, and requesting guide name. |
| `POST /guide/swap-accept` | `swap_request_id` (required) | Looks up the swap request; updates `schedule.guide_id` to the requesting guide; inserts a log row with `action = 'SWAP_ACCEPTED'`. Returns `{"status": "accepted", "schedule_id", "guide_id"}` or `{"status": "not_found"}`. |
| `POST /guide/swap-reject` | `swap_request_id` (required) | Looks up the swap request; inserts a log row with `action = 'SWAP_REJECTED'`. Does not change the schedule. Returns `{"status": "rejected", ...}` or `{"status": "not_found"}`. |

On any service error, routes return `200` with `{"error": "Internal server error"}` and log the exception.

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
