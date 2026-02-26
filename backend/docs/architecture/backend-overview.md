# Backend Architecture Overview

| Field            | Detail                                  |
| ---------------- | --------------------------------------- |
| **Project**      | Oceanarium Tour Scheduling System       |
| **Author**       | Evandro Maciel                          |
| **Last Updated** | February 26, 2026                       |
| **Stack**        | Python 3.12 / FastAPI / SQLAlchemy / PostgreSQL |

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
│   │   ├── guide.py            #   Guide, Language, guide_languages, guide_tour_types
│   │   ├── availability.py     #   AvailabilityPattern, Slot, Exception
│   │   ├── tour.py             #   Tour
│   │   ├── booking.py          #   Booking
│   │   ├── booking_version.py  #   BookingVersion (immutable temporal snapshots)
│   │   ├── customer.py         #   Customer
│   │   ├── schedule.py         #   Schedule (guide-to-booking assignments)
│   │   ├── cost.py             #   Cost (ticket pricing with validity periods)
│   │   ├── resource.py         #   Resource (physical resources)
│   │   ├── tour_resource.py    #   TourResource (tour ↔ resource junction)
│   │   ├── survey.py           #   Survey (post-visit feedback)
│   │   ├── poll_execution.py   #   PollExecution (Clorian polling cycles)
│   │   ├── sync_log.py         #   SyncLog (sync audit)
│   │   ├── audit_log.py        #   TourAssignmentLog (assignment audit trail)
│   │   ├── user.py             #   User (application users)
│   │   └── issue.py            #   Issue (operational issue tracker)
│   │
│   ├── schemas/                # Pydantic models (request/response validation)
│   │   ├── guide.py            #   GuideCreate, GuideUpdate, AvailabilitySetIn, GuideOut
│   │   ├── booking.py          #   BookingCreate, BookingReschedule, BookingOut
│   │   ├── tour.py             #   TourCreate, TourUpdate, ManualAssignIn
│   │   ├── customer.py         #   CustomerCreate, CustomerUpdate, CustomerOut
│   │   ├── schedule.py         #   ScheduleCreate, ScheduleUpdate, ScheduleOut
│   │   ├── resource.py         #   ResourceCreate, ResourceUpdate, ResourceOut
│   │   ├── cost.py             #   CostCreate, CostUpdate, CostOut
│   │   ├── survey.py           #   SurveyCreate, SurveyUpdate, SurveyOut
│   │   └── user.py             #   UserCreate, UserUpdate, UserOut
│   │
│   ├── routers/                # FastAPI route handlers (one per domain)
│   │   ├── health.py           #   Health check + DB connectivity
│   │   ├── guides.py           #   CRUD for guide profiles + availability
│   │   ├── tours.py            #   Tour CRUD
│   │   ├── bookings.py         #   Booking CRUD + reschedule/cancel
│   │   ├── assignments.py      #   Manual assign/reassign, auto-assign, audit trail
│   │   ├── customers.py        #   Customer CRUD
│   │   ├── schedules.py        #   Schedule CRUD
│   │   ├── resources.py        #   Resource CRUD
│   │   ├── costs.py            #   Cost CRUD
│   │   ├── surveys.py          #   Survey CRUD
│   │   ├── users.py            #   User CRUD
│   │   ├── issues.py           #   Issue reporting
│   │   ├── stats.py            #   Dashboard statistics
│   │   ├── notifications.py    #   Notification feed
│   │   └── sync.py             #   Admin sync trigger + log viewer
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
├── tests/                      # Test suite (224 tests)
│   ├── conftest.py             #   Shared fixtures + factories
│   ├── unit/                   #   Model, schema, service, adapter tests
│   ├── integration/            #   Clorian sync service
│   └── api/                    #   Endpoint tests via TestClient
│
├── docs/                       # Project documentation
│   ├── architecture/           #   Architecture docs (this file)
│   ├── database/               #   ERD and database schema documentation
│   ├── fdr/                    #   Functional Requirements Documents
│   └── insomnia.json           #   Insomnia API collection
│
├── scripts/                    # Helper scripts
│   └── reset-db.sh             #   Wipe DB and re-run migrations
│
├── Dockerfile
├── docker-compose.yml
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
| `guide_matcher.py`   | Evaluates guide eligibility (availability + tour type + language)     |
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
      → Compare with local Booking records
      → For each new/changed booking:
          → assignment.assign_guide_to_booking(booking_version, db)
            → guide_matcher.find_eligible_guides(booking_version, db)
            → Pick best guide (fewest assignments that day)
            → Log to TourAssignmentLog
      → For cancelled bookings:
          → assignment.release_guide_from_schedule(schedule, db)
      → Write SyncLog entry
```

### Manual Assignment (admin)

```
POST /bookings/{id}/assign
  → assignments router
    → assignment.manual_assign(booking, guide, db, assigned_by)
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
Booking ──┬── BookingVersion ──┬── Schedule ──── Guide
          │                   └── Survey         │
          ├── Customer                           ├── GuideLanguage ──── Language
          └── Tour                               ├── GuideTourType ──── Tour
                ├── Cost                          ├── AvailabilityPattern
                ├── TourResource ── Resource      │     ├── AvailabilitySlot
                └── TourAssignmentLog             │     └── AvailabilityException
                                                  └── TourAssignmentLog
PollExecution ── BookingVersion
SyncLog (standalone)
Users (standalone)
Issues (standalone)
```

See the [Database ERD](../database/database-erd.md) for the full schema and table descriptions.

### Tables

| Domain             | Tables                                                                          | Count |
| ------------------ | ------------------------------------------------------------------------------- | ----- |
| **Booking**        | `bookings`, `booking_versions`, `customers`                                     | 3     |
| **Guide**          | `guides`, `languages`, `guide_languages`, `guide_tour_types`                    | 4     |
| **Availability**   | `availability_patterns`, `availability_slots`, `availability_exceptions`        | 3     |
| **Tour & Scheduling** | `tours`, `schedule`, `cost`, `resources`, `tour_resources`                   | 5     |
| **Feedback**       | `surveys`                                                                       | 1     |
| **Sync / Ops**     | `poll_execution`, `sync_logs`, `tour_assignment_logs`                           | 3     |
| **Auth / Standalone** | `users`, `issues`                                                            | 2     |
| **Total**          |                                                                                 | **21** |

---

## 6. API Endpoints

### Health

| Method | Path      | Description                         |
| ------ | --------- | ----------------------------------- |
| GET    | `/health` | Health check with DB connectivity   |

### Guides

| Method | Path                        | Description                        |
| ------ | --------------------------- | ---------------------------------- |
| GET    | `/guides`                   | List all guides with full profiles |
| POST   | `/guides`                   | Create a new guide                 |
| GET    | `/guides/{id}`              | Get guide by ID                    |
| PATCH  | `/guides/{id}`              | Update guide profile               |
| PUT    | `/guides/{id}/availability` | Set availability pattern + slots   |

### Tours

| Method | Path           | Description      |
| ------ | -------------- | ---------------- |
| GET    | `/tours`       | List all tours   |
| POST   | `/tours`       | Create tour      |
| GET    | `/tours/{id}`  | Get tour detail  |
| PATCH  | `/tours/{id}`  | Update tour      |
| DELETE | `/tours/{id}`  | Delete tour      |

### Bookings

| Method | Path                             | Description                   |
| ------ | -------------------------------- | ----------------------------- |
| GET    | `/bookings`                      | List bookings (optional `?status=` filter) |
| GET    | `/bookings/unassigned`           | List unassigned bookings      |
| POST   | `/bookings`                      | Create booking                |
| PATCH  | `/bookings/{id}/reschedule`      | Reschedule booking            |
| PATCH  | `/bookings/{id}/cancel`          | Cancel booking                |

### Assignments

| Method | Path                              | Description                   |
| ------ | --------------------------------- | ----------------------------- |
| POST   | `/bookings/{id}/assign`           | Manual guide assignment       |
| POST   | `/bookings/{id}/reassign`         | Reassign guide to booking     |
| POST   | `/bookings/auto-assign`           | Trigger auto-assignment       |
| GET    | `/bookings/{id}/assignment-log`   | View assignment audit trail   |

### Customers

| Method | Path               | Description         |
| ------ | ------------------ | ------------------- |
| GET    | `/customers`       | List customers      |
| POST   | `/customers`       | Create customer     |
| GET    | `/customers/{id}`  | Get customer detail |
| PATCH  | `/customers/{id}`  | Update customer     |
| DELETE | `/customers/{id}`  | Delete customer     |

### Schedules

| Method | Path               | Description                                               |
| ------ | ------------------ | --------------------------------------------------------- |
| GET    | `/schedules`       | List schedules (optional `?guide_id=` or `?booking_version_id=`) |
| POST   | `/schedules`       | Create schedule     |
| GET    | `/schedules/{id}`  | Get schedule detail |
| PATCH  | `/schedules/{id}`  | Update schedule     |
| DELETE | `/schedules/{id}`  | Delete schedule     |

### Resources

| Method | Path               | Description         |
| ------ | ------------------ | ------------------- |
| GET    | `/resources`       | List resources      |
| POST   | `/resources`       | Create resource     |
| GET    | `/resources/{id}`  | Get resource detail |
| PATCH  | `/resources/{id}`  | Update resource     |
| DELETE | `/resources/{id}`  | Delete resource     |

### Costs

| Method | Path            | Description                         |
| ------ | --------------- | ----------------------------------- |
| GET    | `/costs`        | List costs (optional `?tour_id=`)   |
| POST   | `/costs`        | Create cost                         |
| GET    | `/costs/{id}`   | Get cost detail                     |
| PATCH  | `/costs/{id}`   | Update cost                         |
| DELETE | `/costs/{id}`   | Delete cost                         |

### Surveys

| Method | Path              | Description        |
| ------ | ----------------- | ------------------ |
| GET    | `/surveys`        | List surveys       |
| POST   | `/surveys`        | Create survey      |
| GET    | `/surveys/{id}`   | Get survey detail  |
| PATCH  | `/surveys/{id}`   | Update survey      |
| DELETE | `/surveys/{id}`   | Delete survey      |

### Users

| Method | Path            | Description       |
| ------ | --------------- | ----------------- |
| GET    | `/users`        | List users        |
| POST   | `/users`        | Create user       |
| GET    | `/users/{id}`   | Get user detail   |
| PATCH  | `/users/{id}`   | Update user       |
| DELETE | `/users/{id}`   | Delete user       |

### Issues

| Method | Path      | Description      |
| ------ | --------- | ---------------- |
| POST   | `/issues` | Report an issue  |

### Stats & Notifications

| Method | Path             | Description          |
| ------ | ---------------- | -------------------- |
| GET    | `/stats`         | Dashboard statistics |
| GET    | `/notifications` | Notification feed    |

### Sync

| Method | Path            | Description                  |
| ------ | --------------- | ---------------------------- |
| POST   | `/sync/trigger` | Manually trigger Clorian sync |
| GET    | `/sync/logs`    | View sync history (paginated) |

---

## 7. Testing Strategy

```
tests/
├── conftest.py                    # PostgreSQL test DB, shared factories, TestClient
├── unit/                          # Pure logic tests (no HTTP)
│   ├── test_models.py                (19 tests)
│   ├── test_schemas.py               (26 tests)
│   ├── test_guide_matcher.py         (18 tests)
│   ├── test_assignment.py            (8 tests)
│   ├── test_db.py                    (3 tests)
│   ├── test_adapters.py              (9 tests)
│   └── test_sync_scheduler.py        (4 tests)
├── integration/                   # Service-level tests with DB
│   └── test_clorian_sync.py         (14 tests)
└── api/                           # Full HTTP endpoint tests
    ├── test_health_api.py            (2 tests)
    ├── test_guides_api.py            (11 tests)
    ├── test_tours_api.py             (9 tests)
    ├── test_bookings_api.py          (16 tests)
    ├── test_assignments_api.py       (13 tests)
    ├── test_customers_api.py         (9 tests)
    ├── test_schedules_api.py         (14 tests)
    ├── test_resources_api.py         (9 tests)
    ├── test_costs_api.py             (10 tests)
    ├── test_surveys_api.py           (8 tests)
    ├── test_users_api.py             (9 tests)
    ├── test_issues_api.py            (4 tests)
    ├── test_stats_api.py             (2 tests)
    ├── test_notifications_api.py     (2 tests)
    └── test_sync_api.py              (5 tests)
```

**224 tests total** (87 unit + 14 integration + 123 API) covering all acceptance criteria from FDR-001 plus full CRUD coverage for every domain.

Run the full suite:

```bash
cd backend && python3 -m pytest tests/ -v
```

With coverage:

```bash
cd backend && python3 -m pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## 8. Key Design Decisions

| Decision                          | Rationale                                                                 |
| --------------------------------- | ------------------------------------------------------------------------- |
| **Layered architecture**          | Separates HTTP handling from business logic, making services independently testable |
| **Adapter pattern for Clorian**   | Allows mock implementation now, real HTTP client later, without changing services |
| **Booking versioning (immutable snapshots)** | Each change creates a new `BookingVersion` with a content hash, preserving full history for auditability |
| **APScheduler (not Celery)**      | Lightweight in-process scheduler suitable for a single-instance deployment |
| **Alembic for migrations**        | Versioned, reproducible schema changes tracked in git                     |
| **App factory pattern**           | Enables different configurations for production vs testing                |
| **Request-scoped DB sessions**    | Prevents connection leaks; each request gets its own session via `get_db` |
| **Audit log table**               | Every assignment change is traceable (NFR-02 compliance)                  |
| **Tour type matching (not expertise)** | Guides are linked to specific tours they can lead via `guide_tour_types`, simplifying eligibility checks |

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

---

## Revision History

| Version | Date           | Author          | Changes                                               |
| ------- | -------------- | --------------- | ----------------------------------------------------- |
| 1.0     | Feb 25, 2026   | Evandro Maciel  | Initial version                                       |
| 1.1     | Feb 26, 2026   | Evandro Maciel  | Full update: added all 21 tables, 50+ endpoints, 224 tests, booking versioning model, corrected data flow |
