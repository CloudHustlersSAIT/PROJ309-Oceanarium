# Backend Architecture Overview

| Field            | Detail                                  |
| ---------------- | --------------------------------------- |
| **Project**      | Oceanarium Tour Scheduling System       |
| **Author**       | Evandro Maciel                          |
| **Last Updated** | February 25, 2026                       |
| **Stack**        | Python 3.9+ / FastAPI / SQLAlchemy / PostgreSQL |

---

## 1. High-Level Architecture

The backend follows a **layered architecture** with clear separation of concerns. External requests flow through routers into services, which operate on models via the database layer. External systems are accessed through adapters.

```
┌─────────────────────────────────────────────────────────┐
│                      FastAPI App                        │
│                    (main.py + CORS)                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│   │  Routers │  │  Schemas │  │   Jobs   │              │
│   │ (API)    │  │ (I/O)    │  │ (Cron)   │              │
│   └────┬─────┘  └──────────┘  └────┬─────┘              │
│        │                           │                    │
│   ┌────▼───────────────────────────▼────┐               │
│   │            Services                 │               │
│   │  (Business Logic + Orchestration)   │               │
│   └────┬────────────────────────────┬───┘               │
│        │                            │                   │
│   ┌────▼─────┐               ┌──────▼────┐              │
│   │  Models  │               │  Adapters │              │
│   │  (ORM)   │               │ (External)│              │
│   └────┬─────┘               └───────────┘              │
│        │                                                │
│   ┌────▼─────┐                                          │
│   │   db.py  │                                          │
│   │ (Engine) │                                          │
│   └────┬─────┘                                          │
│        │                                                │
└────────┼────────────────────────────────────────────────┘
         │
    ┌────▼─────┐
    │PostgreSQL│
    └──────────┘
```

---

## 2. Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # App factory, CORS, lifespan, router registration
│   ├── db.py                   # SQLAlchemy engine, session, Base, get_db dependency
│   │
│   ├── models/                 # SQLAlchemy ORM models (database tables)
│   │   ├── guide.py            #   Guide, Language, Expertise, association tables
│   │   ├── availability.py     #   AvailabilityPattern, Slot, Exception
│   │   ├── tour.py             #   Tour (synced from Clorian)
│   │   ├── audit_log.py        #   TourAssignmentLog
│   │   └── sync_log.py         #   SyncLog
│   │
│   ├── schemas/                # Pydantic models (request/response validation)
│   │   ├── guide.py            #   GuideCreate, GuideUpdate, AvailabilitySetIn, GuideOut
│   │   ├── tour.py             #   TourOut, ManualAssignIn, AssignmentLogOut, SyncLogOut
│   │   └── booking.py          #   BookingCreate, BookingReschedule
│   │
│   ├── routers/                # FastAPI route handlers (one per domain)
│   │   ├── guides.py           #   CRUD for guide profiles + availability
│   │   ├── tours.py            #   Tour listing + detail + unassigned filter
│   │   ├── assignments.py      #   Manual assign/reassign + audit trail
│   │   ├── bookings.py         #   Legacy booking endpoints
│   │   ├── sync.py             #   Admin sync trigger + log viewer
│   │   ├── health.py           #   Health check + DB connectivity
│   │   ├── issues.py           #   Issue reporting
│   │   ├── stats.py            #   Dashboard statistics
│   │   └── notifications.py    #   Notification feed
│   │
│   ├── services/               # Business logic (framework-agnostic)
│   │   ├── guide_matcher.py    #   find_eligible_guides() — 3-rule AND matching
│   │   ├── assignment.py       #   Auto-assign, manual override, release, audit log
│   │   └── clorian_sync.py     #   Sync orchestration, change detection, failure tracking
│   │
│   ├── jobs/                   # Scheduled background tasks
│   │   └── sync_scheduler.py   #   APScheduler 15-min job with overlap guard
│   │
│   └── adapters/               # External system integrations
│       ├── clorian_client.py   #   Abstract ClorianClientBase interface
│       └── clorian_mock.py     #   Mock implementation for dev/testing
│
├── alembic/                    # Database migration scripts
├── alembic.ini
├── tests/                      # Test suite (52 tests)
│   ├── conftest.py             #   Shared fixtures + factories
│   ├── unit/                   #   Guide matcher + assignment logic
│   ├── integration/            #   Clorian sync service
│   └── api/                    #   Endpoint tests via TestClient
│
├── docs/                       # Project documentation
│   ├── fdr/                    #   Functional Requirements Documents
│   ├── architecture/           #   Architecture docs (this file)
│   └── insomnia.json           #   Insomnia API collection
│
└── requirements.txt
```

---

## 3. Layer Responsibilities

### Routers (`app/routers/`)

HTTP request handling only. Routers parse input, call services, and return responses. They never contain business logic.

- Receive HTTP requests and validate input via Pydantic schemas.
- Inject database sessions via the `get_db` dependency.
- Delegate work to the **services** layer.
- Return structured JSON responses.

### Services (`app/services/`)

All business logic lives here. Services are framework-agnostic — they receive a SQLAlchemy `Session` and model objects, making them easy to test without HTTP.

| Service              | Responsibility                                                       |
| -------------------- | -------------------------------------------------------------------- |
| `guide_matcher.py`   | Evaluates guide eligibility (availability + expertise + language)     |
| `assignment.py`      | Orchestrates auto-assignment, manual override, release, audit logging |
| `clorian_sync.py`    | Pulls bookings from Clorian, detects changes, triggers assignment    |

### Models (`app/models/`)

SQLAlchemy ORM classes that map to PostgreSQL tables. Relationships are defined here (e.g., Guide ↔ Language via association table). No business logic in models.

### Schemas (`app/schemas/`)

Pydantic models for request/response serialization and validation. Decoupled from ORM models so the API contract can evolve independently of the database schema.

### Adapters (`app/adapters/`)

Abstraction layer for external systems. Each external dependency has an abstract base class and one or more concrete implementations:

- `ClorianClientBase` (abstract) → `ClorianMockClient` (dev/test)
- When the real Clorian API is available, a `ClorianHttpClient` will implement the same interface.

### Jobs (`app/jobs/`)

Background tasks run by APScheduler. The sync scheduler runs every 15 minutes and includes a thread lock to prevent overlapping executions.

---

## 4. Data Flow

### Clorian Sync → Guide Assignment (automated)

```
APScheduler (every 15 min)
  → sync_scheduler.run_sync_job()
    → ClorianSyncService.run_sync(db)
      → ClorianClient.fetch_bookings()
      → Compare with local Tour records
      → For each new/changed tour:
          → assignment.assign_guide_to_tour(tour, db)
            → guide_matcher.find_eligible_guides(tour, db)
            → Pick best guide (fewest tours that day)
            → Log to TourAssignmentLog
      → For cancelled tours:
          → assignment.release_guide(tour, db)
      → Write SyncLog entry
```

### Manual Assignment (admin)

```
POST /tours/{id}/assign
  → assignments router
    → assignment.manual_assign(tour, guide, db, assigned_by)
      → Bypasses suitability rules
      → Releases previous guide if any
      → Logs to TourAssignmentLog with type="manual"
```

---

## 5. Database

### Engine

- **ORM**: SQLAlchemy 2.x with `declarative_base`
- **Driver**: `psycopg2-binary` (PostgreSQL)
- **Sessions**: Managed via `get_db()` FastAPI dependency (request-scoped)
- **Migrations**: Alembic with autogenerate support

### Entity Relationship Diagram

```
Guide ──┬── GuideLanguage ──── Language
        ├── GuideExpertise ─── Expertise
        ├── AvailabilityPattern ──┬── AvailabilitySlot
        │                        └── AvailabilityException
        └── Tour (assigned_guide_id)
                └── TourAssignmentLog

SyncLog (standalone)
```

### Tables

| Table                      | Purpose                                        |
| -------------------------- | ---------------------------------------------- |
| `guides`                   | Guide profiles (name, email, active status)    |
| `languages`                | Language reference data (code, name)           |
| `expertises`               | Expertise reference data (name, category)      |
| `guide_languages`          | Many-to-many: guide ↔ language                 |
| `guide_expertises`         | Many-to-many: guide ↔ expertise                |
| `availability_patterns`    | One per guide: timezone config                 |
| `availability_slots`       | Recurring weekly slots (day, start, end)       |
| `availability_exceptions`  | Date-specific overrides (blocked, note)        |
| `tours`                    | Synced from Clorian, with assignment status    |
| `tour_assignment_logs`     | Audit trail for all assignment changes         |
| `sync_logs`                | Record of each Clorian sync cycle              |

---

## 6. API Endpoints

| Method | Path                           | Router       | Description                        |
| ------ | ------------------------------ | ------------ | ---------------------------------- |
| GET    | `/health`                      | health       | Basic health check                 |
| GET    | `/health/db`                   | health       | Database connectivity check        |
| GET    | `/guides`                      | guides       | List all guides with full profiles |
| POST   | `/guides`                      | guides       | Create a new guide                 |
| GET    | `/guides/{id}`                 | guides       | Get guide by ID                    |
| PATCH  | `/guides/{id}`                 | guides       | Update guide profile               |
| PUT    | `/guides/{id}/availability`    | guides       | Set availability pattern + slots   |
| GET    | `/tours`                       | tours        | List all tours                     |
| GET    | `/tours/unassigned`            | tours        | List unassigned tours              |
| GET    | `/tours/{id}`                  | tours        | Get tour detail                    |
| POST   | `/tours/{id}/assign`           | assignments  | Manual guide assignment            |
| POST   | `/tours/{id}/reassign`         | assignments  | Reassign guide to tour             |
| GET    | `/tours/{id}/assignment-log`   | assignments  | View assignment audit trail        |
| GET    | `/bookings`                    | bookings     | List bookings                      |
| POST   | `/bookings`                    | bookings     | Create booking                     |
| PATCH  | `/bookings/{id}/reschedule`    | bookings     | Reschedule booking                 |
| PATCH  | `/bookings/{id}/cancel`        | bookings     | Cancel booking                     |
| POST   | `/issues`                      | issues       | Report an issue                    |
| GET    | `/stats`                       | stats        | Dashboard statistics               |
| GET    | `/notifications`               | notifications| Notification feed                  |
| POST   | `/sync/trigger`                | sync         | Manually trigger Clorian sync      |
| GET    | `/sync/logs`                   | sync         | View sync history                  |

---

## 7. Testing Strategy

```
tests/
├── conftest.py           # In-memory SQLite, shared factories, TestClient
├── unit/                 # Pure logic tests (no HTTP)
│   ├── test_guide_matcher.py   (22 tests)
│   └── test_assignment.py      (8 tests)
├── integration/          # Service-level tests with DB
│   └── test_clorian_sync.py    (10 tests)
└── api/                  # Full HTTP endpoint tests
    ├── test_guides_api.py       (4 tests)
    ├── test_tours_api.py        (3 tests)
    ├── test_assignments_api.py  (3 tests)
    └── test_sync_api.py         (2 tests)
```

**52 tests total** covering all 12 acceptance criteria from FDR-001.

Run the full suite:

```bash
cd backend && python3 -m pytest tests/ -v
```

---

## 8. Key Design Decisions

| Decision                          | Rationale                                                                 |
| --------------------------------- | ------------------------------------------------------------------------- |
| **Layered architecture**          | Separates HTTP handling from business logic, making services independently testable |
| **Adapter pattern for Clorian**   | Allows mock implementation now, real HTTP client later, without changing services |
| **APScheduler (not Celery)**      | Lightweight in-process scheduler suitable for a single-instance deployment |
| **Alembic for migrations**        | Versioned, reproducible schema changes tracked in git                     |
| **App factory pattern**           | Enables different configurations for production vs testing                |
| **Request-scoped DB sessions**    | Prevents connection leaks; each request gets its own session via `get_db` |
| **Audit log table**               | Every assignment change is traceable (NFR-02 compliance)                  |

---

## 9. Dependencies

| Package            | Purpose                                |
| ------------------ | -------------------------------------- |
| `fastapi[standard]`| Web framework + Uvicorn server         |
| `sqlalchemy`       | ORM and database toolkit               |
| `psycopg2-binary`  | PostgreSQL driver                      |
| `python-dotenv`    | Environment variable management        |
| `alembic`          | Database migration tool                |
| `apscheduler`      | Background job scheduling              |
| `httpx`            | Async HTTP client (for future Clorian) |
| `pytest`           | Test runner                            |
| `pytest-cov`       | Test coverage reporting                |
