# [ADR-002] Adopt Layered Domain Architecture

| Field            | Value                  |
|------------------|------------------------|
| **ID**           | ADR-002                |
| **Version**      | 2.1                    |
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

As we build out 8 bounded contexts (Reservation, Scheduling, Guide, Availability, Feedback, Notification, Sync, Auth) with 20+ tables (see ERD v4.0), this structure will not scale. Key problems:

- **No separation of concerns**: routes, business logic, and data access are interleaved
- **No ORM models**: tables are accessed via raw `text()` SQL with no type safety
- **No migrations**: schema is not version-controlled
- **No testability**: business logic is tightly coupled to SQL execution and HTTP routing
- **No adapter pattern**: future Clorian integration will be tightly coupled to domain logic

## Decision

**Adopt a layer-first architecture where each folder represents a layer, and each file within a layer corresponds to a domain/bounded context.**

### Target Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                          ← App factory (create_app, CORS, include routers)
│   ├── config.py                        ← Pydantic Settings (DATABASE_URL, CORS, intervals)
│   │
│   ├── routes/                          ← HTTP layer — thin, delegates to services
│   │   ├── __init__.py
│   │   ├── reservation.py               ← /reservations, /reservations/{id}
│   │   ├── scheduling.py                ← /schedules, /schedules/{id}/assign
│   │   ├── guide.py                     ← /guides
│   │   ├── availability.py              ← /guides/{id}/availability
│   │   ├── notification.py              ← /notifications
│   │   ├── feedback.py                  ← /surveys
│   │   ├── sync.py                      ← /admin/poll/trigger
│   │   └── auth.py                      ← /auth/login, /users
│   │
│   ├── schemas/                         ← Pydantic DTOs (request/response)
│   │   ├── __init__.py
│   │   ├── reservation.py
│   │   ├── scheduling.py
│   │   ├── guide.py
│   │   ├── availability.py
│   │   ├── notification.py
│   │   ├── feedback.py
│   │   ├── sync.py
│   │   └── auth.py
│   │
│   ├── services/                        ← Business logic, validation, orchestration
│   │   ├── __init__.py
│   │   ├── reservation.py               ← Ingestion, versioning, hash detection
│   │   ├── scheduling.py                ← ScheduleBuilder, ReScheduling
│   │   ├── guide_assignment.py          ← 3 constraints + priority
│   │   ├── availability.py              ← AvailabilityQuery
│   │   ├── notification.py              ← Portal + email dispatch
│   │   ├── feedback.py
│   │   └── sync.py                      ← ClorianPoller orchestration
│   │
│   ├── repositories/                    ← Data access — all SQL/ORM queries
│   │   ├── __init__.py
│   │   ├── customer.py
│   │   ├── reservation.py
│   │   ├── ticket.py
│   │   ├── schedule.py
│   │   ├── guide.py
│   │   ├── availability.py
│   │   ├── notification.py
│   │   ├── survey.py
│   │   ├── poll_execution.py
│   │   ├── sync_log.py
│   │   ├── tour_assignment_log.py
│   │   └── user.py
│   │
│   ├── models/                          ← SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── customer.py                  ← Customer
│   │   ├── reservation.py               ← Reservation, ReservationVersion
│   │   ├── ticket.py                    ← Ticket
│   │   ├── tour.py                      ← Tour
│   │   ├── schedule.py                  ← Schedule
│   │   ├── guide.py                     ← Guide, GuideLanguage, GuideTourType
│   │   ├── language.py                  ← Language
│   │   ├── availability.py              ← AvailabilityPattern, AvailabilitySlot, AvailabilityException
│   │   ├── notification.py              ← Notification
│   │   ├── survey.py                    ← Survey
│   │   ├── poll_execution.py            ← PollExecution
│   │   ├── sync_log.py                  ← SyncLog
│   │   ├── tour_assignment_log.py       ← TourAssignmentLog
│   │   └── user.py                      ← User
│   │
│   ├── infrastructure/                  ← Cross-cutting technical concerns
│   │   ├── __init__.py
│   │   ├── database.py                  ← Engine, session factory, declarative Base
│   │   └── email.py                     ← Email client (SMTP/SES)
│   │
│   └── adapters/                        ← External system integrations
│       └── clorian/
│           ├── __init__.py
│           ├── client.py                ← HTTP client for Clorian API
│           ├── mapper.py                ← Clorian JSON → domain models (ACL)
│           └── schemas.py               ← Pydantic models for raw Clorian payloads
│
├── migrations/                          ← Alembic version-controlled migrations
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│
├── tests/                               ← Mirrors layer structure
│   ├── routes/
│   ├── services/
│   ├── repositories/
│   └── adapters/
│       └── clorian/
│
├── docs/                                ← Already organized
├── Dockerfile
├── requirements.txt
└── .env
```

### Layer Responsibilities

| Layer | Folder | Responsibility | Depends On |
|-------|--------|---------------|------------|
| **Routes** | `routes/` | Parse HTTP request, call service, return response. No business logic, no SQL. | schemas, services |
| **Schemas** | `schemas/` | Pydantic models for API request/response DTOs. Decoupled from DB models. | — |
| **Services** | `services/` | Business logic, validation, orchestration, domain event emission. | repositories, other services |
| **Repositories** | `repositories/` | Data access — all SQL/ORM queries live here. Single source of truth for DB operations. | models, infrastructure |
| **Models** | `models/` | SQLAlchemy ORM models with relationships, constraints, and column definitions. | infrastructure |
| **Infrastructure** | `infrastructure/` | Cross-cutting: DB engine, session management, email client, shared middleware. | config |
| **Adapters** | `adapters/` | External system integration. Translates external data formats into our models. | schemas, models |
| **Config** | `config.py` | Centralized settings via Pydantic Settings (env vars, defaults). | — |

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

### Implementation Phases

This architecture will be adopted incrementally to minimize risk and keep the application deployable at every step. Each phase produces a working backend — no phase leaves the codebase in a broken state.

| Phase | Scope | Layers touched | New decision? |
|-------|-------|---------------|---------------|
| 1 | Route/service extraction — split `main.py` monolith into thin routes and service functions. Raw SQL stays in services temporarily. | `routes/`, `services/` | No (this ADR) |
| 2 | ORM models + repository pattern — replace raw `text()` SQL with SQLAlchemy models and repository functions. | `models/`, `repositories/` | Yes → ADR-003 |
| 3 | Pydantic schemas (DTOs) — extract request/response models from route files into a dedicated schemas layer. | `schemas/` | No (this ADR) |
| 4 | Infrastructure + config — centralize DB engine, session factory, and settings into `infrastructure/` and `config.py`. | `infrastructure/`, `config.py` | No (this ADR) |
| 5 | Alembic migrations — version-controlled schema changes. | `migrations/` | Yes → ADR-004 |
| 6 | Clorian adapter — HTTP client, mapper (ACL), and external payload schemas. | `adapters/clorian/` | Yes → ADR-005 |

Phases 2, 5, and 6 introduce genuinely new technical decisions (ORM choice, migration tooling, external integration pattern) that warrant their own ADRs with alternatives considered.

## Options Considered

### Option A: Flat file structure (one file per resource, prefixed by layer)

```
app/
├── routes_reservation.py
├── routes_guide.py
├── services_reservation.py
├── models_reservation.py
└── ...
```

- **Pros**: Simple, no nesting
- **Cons**: Files grow large, naming convention is the only grouping, no visual separation between layers

### Option B: Domain-first (vertical slices per bounded context)

```
app/domain/reservation/{models, schemas, repository, service, routes}.py
```

- **Pros**: High cohesion within a domain, everything about reservations in one place
- **Cons**: When working on a layer across domains (e.g., all routes or all models), you have to jump between many folders; harder to enforce consistent patterns across a layer

### Option C: Layer-first architecture (chosen)

```
app/routes/reservation.py
app/services/reservation.py
app/repositories/reservation.py
app/models/reservation.py
```

- **Pros**:
  - Easy to find all files of the same type — "open `routes/` and you see every endpoint"
  - Natural for code reviews: reviewing a route change means opening `routes/` and `schemas/`
  - Enforces consistent patterns within a layer (all repositories follow the same shape)
  - Familiar to most Python/FastAPI developers
  - Each layer folder acts as a guardrail — new contributors know exactly where to put code
  - Domain is expressed by filename, layer is expressed by folder
- **Cons**:
  - Related files for one domain are spread across folders (e.g., reservation logic in 5 different folders)
  - Mitigated by consistent naming: `reservation.py` in every layer folder makes cross-referencing easy

### Option D: Full hexagonal / ports-and-adapters

- **Pros**: Maximum decoupling, framework-agnostic domain core
- **Cons**: Over-engineered for a team and project of this size, adds abstract interfaces and indirection that slow development

## Consequences

### Positive

- Each file is small, focused, and has a single responsibility
- Layer folders act as **guardrails** — new contributors know exactly where routes, services, and models go
- Consistent naming (`reservation.py` in `routes/`, `services/`, `repositories/`, `models/`) makes navigation intuitive
- Business logic is testable without HTTP or database (mock the repository layer)
- Raw SQL is eliminated in favor of ORM — schema changes tracked by Alembic
- Clorian integration is isolated — API changes only affect `adapters/clorian/`
- Adding a new domain means adding one file per layer, not creating a new folder tree

### Negative

- More files to manage compared to current 4-file structure
- Requires learning SQLAlchemy ORM and Alembic if team is unfamiliar
- Initial migration effort to move existing code from `main.py` into the new structure
- Related domain code is spread across multiple folders (mitigated by consistent file naming)

### Risks

- Thin domains (e.g., feedback) may only need a model + route — empty service/repository files are fine to omit until needed
- Cross-domain queries (e.g., stats dashboard) may need to import multiple repositories — this is acceptable for read-only query services

## Related

- [ADR-001] Naming & Structure — Reservation naming, no purchases table
- [ADR-003] Adopt SQLAlchemy ORM (future — Phase 2)
- [ADR-004] Adopt Alembic for Migrations (future — Phase 5)
- [ADR-005] Clorian Adapter Pattern (future — Phase 6)
- [DDD-001] Domain Model Overview — defines the 8 bounded contexts
- [FDR-001] Reservation Ingestion — drives the adapter/clorian structure
- [FDR-002] Guide Assignment — drives the guide/scheduling service split
- [FDR-003] Notifications — drives the notification layer files
- [FDR-004] Auto Re-scheduling — drives the scheduling service complexity
- [DB] ERD v4.0 — defines the 20+ tables that map to ORM models

## Changelog

| Version | Date       | Author          | Description |
|---------|------------|-----------------|-------------|
| 1.0     | 2026-03-03 | Evandro Maciel | Initial proposal — domain-first vertical slices |
| 1.1     | 2026-03-03 | Evandro Maciel | Renamed booking domain → reservation domain |
| 2.0     | 2026-03-03 | Evandro Maciel | Switched to layer-first architecture (folders by layer, files by domain); reorganized options considered; updated consequences |
| 2.1     | 2026-03-03 | Evandro Maciel | Added implementation phases table; linked future ADRs (003–005) for ORM, migrations, and Clorian adapter |
