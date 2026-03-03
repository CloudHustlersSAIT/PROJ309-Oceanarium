# [ADR-002] Adopt Layered Domain Architecture

| Field            | Value                  |
|------------------|------------------------|
| **ID**           | ADR-002                |
| **Version**      | 1.0                    |
| **Status**       | Proposed               |
| **Author**       | Evandro Maciel         |
| **Created**      | 2026-03-03             |
| **Last Updated** | 2026-03-03             |

---

## Context

The current backend consists of 4 Python files:

```
backend/app/
├── __init__.py
├── db.py           ← engine + session
├── main.py         ← 422 lines: routes, schemas, business logic, raw SQL, CORS config
└── mock_poller.py  ← routes + DB operations + data generation in one file
```

`main.py` is a monolith mixing every concern: route definitions, Pydantic schemas, validation logic, conflict detection, raw SQL queries, and app configuration.

As we build out 8 bounded contexts (Booking, Scheduling, Guide, Availability, Feedback, Notification, Sync, Auth) with 20+ tables (see ERD v3.0), this structure will not scale. Key problems:

- **No separation of concerns**: routes, business logic, and data access are interleaved
- **No ORM models**: tables are accessed via raw `text()` SQL with no type safety
- **No migrations**: schema is not version-controlled
- **No testability**: business logic is tightly coupled to SQL execution and HTTP routing
- **No adapter pattern**: future Clorian integration will be tightly coupled to domain logic

## Decision

**Adopt a layered domain architecture organized by bounded context, with clear separation into routes, services, repositories, models, schemas, adapters, and infrastructure.**

### Target Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  ← App factory (create_app, CORS, include routers)
│   ├── config.py                ← Pydantic Settings (DATABASE_URL, CORS, intervals)
│   │
│   ├── infrastructure/          ← Cross-cutting technical concerns
│   │   ├── database.py          ← Engine, session factory, declarative Base
│   │   └── email.py             ← Email client (SMTP/SES)
│   │
│   ├── domain/                  ← Vertical slices per bounded context
│   │   ├── booking/
│   │   │   ├── models.py        ← SQLAlchemy ORM (Customer, Purchase, Booking, BookingVersion, Ticket)
│   │   │   ├── schemas.py       ← Pydantic DTOs (request/response)
│   │   │   ├── repository.py    ← Data access (queries, upserts)
│   │   │   ├── service.py       ← Business logic (ingestion, versioning, hash detection)
│   │   │   └── routes.py        ← FastAPI router (thin — delegates to service)
│   │   │
│   │   ├── scheduling/
│   │   │   ├── models.py        ← Schedule, TourAssignmentLog
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── service.py       ← ScheduleBuilder, ReScheduling
│   │   │   └── routes.py
│   │   │
│   │   ├── guide/
│   │   │   ├── models.py        ← Guide, GuideLanguage, GuideTourType
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── service.py       ← GuideAssignment (3 constraints + priority)
│   │   │   └── routes.py
│   │   │
│   │   ├── availability/
│   │   │   ├── models.py
│   │   │   ├── repository.py
│   │   │   ├── service.py       ← AvailabilityQuery
│   │   │   └── routes.py
│   │   │
│   │   ├── notification/
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── service.py       ← Portal + email dispatch
│   │   │   └── routes.py
│   │   │
│   │   ├── feedback/
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   └── routes.py
│   │   │
│   │   ├── sync/
│   │   │   ├── models.py        ← PollExecution, SyncLog
│   │   │   ├── repository.py
│   │   │   ├── service.py       ← ClorianPoller
│   │   │   └── routes.py        ← POST /admin/poll/trigger
│   │   │
│   │   └── auth/
│   │       ├── models.py
│   │       ├── schemas.py
│   │       ├── repository.py
│   │       ├── service.py
│   │       └── routes.py
│   │
│   └── adapters/                ← External system integrations
│       └── clorian/
│           ├── client.py        ← HTTP client for Clorian API
│           ├── mapper.py        ← Clorian JSON → domain models (Anti-Corruption Layer)
│           └── schemas.py       ← Pydantic models for raw Clorian payloads
│
├── migrations/                  ← Alembic version-controlled migrations
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│
├── tests/                       ← Mirrors domain structure
│   ├── domain/
│   │   ├── booking/
│   │   ├── scheduling/
│   │   └── ...
│   └── adapters/
│       └── clorian/
│
├── docs/                        ← Already organized
├── Dockerfile
├── requirements.txt
└── .env
```

### Layer Responsibilities

| Layer | Responsibility | Depends On |
|-------|---------------|------------|
| **routes.py** | Parse HTTP request, call service, return response. No business logic, no SQL. | schemas, service |
| **schemas.py** | Pydantic models for API request/response DTOs. Decoupled from DB models. | — |
| **service.py** | Business logic, validation, orchestration, domain event emission. | repository, other services |
| **repository.py** | Data access — all SQL/ORM queries live here. Single source of truth for DB operations. | models, database |
| **models.py** | SQLAlchemy ORM models with relationships, constraints, and column definitions. | infrastructure/database |
| **infrastructure/** | Cross-cutting: DB engine, session management, email client, shared middleware. | config |
| **adapters/** | External system integration. Translates external data formats into domain models. | domain schemas/models |
| **config.py** | Centralized settings via Pydantic Settings (env vars, defaults). | — |

### Dependency Direction (strict)

```
routes → services → repositories → models
                  → adapters
          infrastructure ← (injected via FastAPI Depends)
```

No layer may import from a layer above it.

### Key Technical Decisions

1. **SQLAlchemy ORM models** replace raw `text()` SQL — enables type safety, relationships, and Alembic migrations
2. **Repository pattern** encapsulates all data access — enables unit testing with mocked repositories
3. **FastAPI `Depends()`** for dependency injection — inject DB sessions and services into routes
4. **Pydantic Settings** for configuration — type-safe, validates at startup
5. **Alembic** for database migrations — version-controlled schema changes
6. **Adapter pattern** for Clorian — Anti-Corruption Layer isolates external data formats

## Options Considered

### Option A: Flat file structure (one file per resource)

```
app/
├── routes_booking.py
├── routes_guide.py
├── services_booking.py
├── models_booking.py
└── ...
```

- **Pros**: Simple, fewer directories
- **Cons**: Files grow large, related code scattered across the folder, poor cohesion, hard to navigate as domains grow

### Option B: Layered domain architecture (chosen)

```
app/domain/booking/{models, schemas, repository, service, routes}.py
```

- **Pros**: High cohesion (everything about bookings in one place), low coupling (clear dependency direction), matches DDD bounded contexts, scales well, easy to test
- **Cons**: More folders/files upfront, slightly higher initial complexity

### Option C: Full hexagonal / ports-and-adapters

- **Pros**: Maximum decoupling, framework-agnostic domain core
- **Cons**: Over-engineered for a team and project of this size, adds abstract interfaces and indirection that slow development

## Consequences

### Positive

- Each file is small, focused, and has a single responsibility
- Adding a new domain (e.g., a future "Resources" context) is a `mkdir` + 5 small files
- Business logic is testable without HTTP or database
- Raw SQL is eliminated in favor of ORM — schema changes tracked by Alembic
- Clorian integration is isolated — API changes only affect `adapters/clorian/`
- Clear onboarding path: "find the domain folder, read routes → service → repository"

### Negative

- More files and directories to manage compared to current 4-file structure
- Requires learning SQLAlchemy ORM and Alembic if team is unfamiliar
- Initial migration effort to move existing code from `main.py` into the new structure

### Risks

- Over-splitting too early: some domains may be thin (e.g., `feedback/` might just be a model + route). Mitigated by allowing thin domains — a folder with fewer files is fine.
- Cross-domain queries: some use cases (e.g., stats dashboard) span multiple domains. Mitigated by a dedicated read-model/query service or allowing controlled cross-repository reads.

## Related

- [ADR-001] Drop Reservation Table
- [DDD-001] Domain Model Overview — defines the 8 bounded contexts this architecture implements
- [FDR-001] Booking Ingestion — drives the adapter/clorian structure
- [FDR-002] Guide Assignment — drives the guide/scheduling service split
- [FDR-003] Notifications — drives the notification domain
- [FDR-004] Auto Re-scheduling — drives the scheduling service complexity
- [DB] ERD v3.0 — defines the 20+ tables that map to ORM models

## Changelog

| Version | Date       | Author          | Description |
|---------|------------|-----------------|-------------|
| 1.0     | 2026-03-03 | Evandro Maciel | Initial proposal — layered domain architecture with adapters |
