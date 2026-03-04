# [DB-001] Initial Schema Migration

| Field            | Value                  |
|------------------|------------------------|
| **ID**           | DB-001                 |
| **Version**      | 1.0                    |
| **Status**       | Active                 |
| **Author**       | Evandro Maciel         |
| **Created**      | 2026-03-04             |
| **Last Updated** | 2026-03-04             |

---

## Overview

Greenfield migration that creates all 19 user-defined tables defined in the [ERD v4.0](ERD.md). Uses raw SQL via Alembic `op.execute()` — no ORM models. Tables are created in foreign-key dependency order so that every `REFERENCES` clause points to an already-existing table.

## Schema

```sql
-- ── Phase A: Independent tables ──

CREATE TABLE customers (
    id              SERIAL PRIMARY KEY,
    clorian_client_id INTEGER NOT NULL UNIQUE,
    first_name      VARCHAR(255) NOT NULL,
    last_name       VARCHAR(255) NOT NULL,
    email           VARCHAR(255)
);

CREATE TABLE tours (
    id                SERIAL PRIMARY KEY,
    clorian_product_id INTEGER NOT NULL UNIQUE,
    name              VARCHAR(255) NOT NULL,
    description       TEXT,
    duration          INTEGER
);

CREATE TABLE languages (
    id   SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(255) NOT NULL UNIQUE,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(255),
    role          VARCHAR(50) NOT NULL,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE guides (
    id           SERIAL PRIMARY KEY,
    first_name   VARCHAR(255) NOT NULL,
    last_name    VARCHAR(255) NOT NULL,
    email        VARCHAR(255),
    phone        VARCHAR(50),
    guide_rating DECIMAL(3,2),
    is_active    BOOLEAN NOT NULL DEFAULT TRUE
);

-- ── Phase B: Single FK to Phase A ──

CREATE TABLE availability_patterns (
    id       SERIAL PRIMARY KEY,
    guide_id INTEGER NOT NULL REFERENCES guides(id),
    timezone VARCHAR(100) NOT NULL
);

CREATE TABLE poll_execution (
    id           SERIAL PRIMARY KEY,
    window_start TIMESTAMPTZ NOT NULL,
    window_end   TIMESTAMPTZ NOT NULL,
    executed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status       VARCHAR(50) NOT NULL
);

-- ── Phase C: FKs to Phase A+B ──

CREATE TABLE availability_slots (
    id          SERIAL PRIMARY KEY,
    pattern_id  INTEGER NOT NULL REFERENCES availability_patterns(id),
    day_of_week VARCHAR(20) NOT NULL,
    start_time  TIME NOT NULL,
    end_time    TIME NOT NULL
);

CREATE TABLE availability_exceptions (
    id         SERIAL PRIMARY KEY,
    pattern_id INTEGER NOT NULL REFERENCES availability_patterns(id),
    date       DATE NOT NULL,
    type       VARCHAR(50) NOT NULL,
    reason     VARCHAR(255)
);

CREATE TABLE guide_languages (
    guide_id    INTEGER NOT NULL REFERENCES guides(id),
    language_id INTEGER NOT NULL REFERENCES languages(id),
    PRIMARY KEY (guide_id, language_id)
);

CREATE TABLE guide_tour_types (
    guide_id INTEGER NOT NULL REFERENCES guides(id),
    tour_id  INTEGER NOT NULL REFERENCES tours(id),
    PRIMARY KEY (guide_id, tour_id)
);

CREATE TABLE sync_logs (
    id                SERIAL PRIMARY KEY,
    poll_execution_id INTEGER NOT NULL REFERENCES poll_execution(id),
    started_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at       TIMESTAMPTZ,
    new_count         INTEGER NOT NULL DEFAULT 0,
    changed_count     INTEGER NOT NULL DEFAULT 0,
    cancelled_count   INTEGER NOT NULL DEFAULT 0,
    status            VARCHAR(50) NOT NULL,
    errors            TEXT
);

CREATE TABLE schedule (
    id                   SERIAL PRIMARY KEY,
    guide_id             INTEGER REFERENCES guides(id),
    tour_id              INTEGER NOT NULL REFERENCES tours(id),
    language_code        VARCHAR(10) NOT NULL,
    event_start_datetime TIMESTAMPTZ NOT NULL,
    event_end_datetime   TIMESTAMPTZ NOT NULL,
    status               VARCHAR(50) NOT NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Phase D: Deeper FK chains ──

CREATE TABLE reservations (
    id                      SERIAL PRIMARY KEY,
    clorian_reservation_id  INTEGER NOT NULL UNIQUE,
    clorian_purchase_id     INTEGER,
    customer_id             INTEGER NOT NULL REFERENCES customers(id),
    tour_id                 INTEGER NOT NULL REFERENCES tours(id),
    schedule_id             INTEGER REFERENCES schedule(id),
    language_code           VARCHAR(10),
    event_start_datetime    TIMESTAMPTZ,
    status                  VARCHAR(50) NOT NULL,
    current_ticket_num      INTEGER NOT NULL DEFAULT 0,
    clorian_created_at      TIMESTAMPTZ,
    clorian_modified_at     TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE reservation_versions (
    id                   SERIAL PRIMARY KEY,
    reservation_id       INTEGER NOT NULL REFERENCES reservations(id),
    hash                 VARCHAR(255) NOT NULL,
    status               VARCHAR(50) NOT NULL,
    current_ticket_num   INTEGER NOT NULL DEFAULT 0,
    language_code        VARCHAR(10),
    event_start_datetime TIMESTAMPTZ,
    received_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_from           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    poll_execution_id    INTEGER NOT NULL REFERENCES poll_execution(id)
);

CREATE TABLE tickets (
    id                  SERIAL PRIMARY KEY,
    clorian_ticket_id   INTEGER NOT NULL UNIQUE,
    reservation_id      INTEGER NOT NULL REFERENCES reservations(id),
    buyer_type_id       INTEGER,
    buyer_type_name     VARCHAR(255),
    start_datetime      TIMESTAMPTZ,
    end_datetime        TIMESTAMPTZ,
    ticket_status       VARCHAR(50) NOT NULL,
    price               DECIMAL(10,2),
    venue_id            INTEGER,
    venue_name          VARCHAR(255),
    clorian_created_at  TIMESTAMPTZ,
    clorian_modified_at TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE surveys (
    id             SERIAL PRIMARY KEY,
    customer_id    INTEGER NOT NULL REFERENCES customers(id),
    guide_id       INTEGER NOT NULL REFERENCES guides(id),
    reservation_id INTEGER NOT NULL REFERENCES reservations(id),
    comment        TEXT,
    rating         INTEGER NOT NULL
);

CREATE TABLE notifications (
    id          SERIAL PRIMARY KEY,
    event_type  VARCHAR(100) NOT NULL,
    schedule_id INTEGER NOT NULL REFERENCES schedule(id),
    guide_id    INTEGER REFERENCES guides(id),
    user_id     INTEGER REFERENCES users(id),
    channel     VARCHAR(50) NOT NULL,
    status      VARCHAR(50) NOT NULL,
    message     TEXT,
    sent_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE tour_assignment_logs (
    id              SERIAL PRIMARY KEY,
    schedule_id     INTEGER NOT NULL REFERENCES schedule(id),
    guide_id        INTEGER NOT NULL REFERENCES guides(id),
    assigned_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    assigned_by     VARCHAR(255) NOT NULL,
    assignment_type VARCHAR(50) NOT NULL,
    action          VARCHAR(50) NOT NULL
);

-- ── Query-path indexes ──

CREATE INDEX ix_reservations_customer_id ON reservations (customer_id);
CREATE INDEX ix_reservations_tour_id ON reservations (tour_id);
CREATE INDEX ix_reservations_schedule_id ON reservations (schedule_id);
CREATE INDEX ix_reservations_status ON reservations (status);
CREATE INDEX ix_reservation_versions_reservation_id ON reservation_versions (reservation_id);
CREATE INDEX ix_reservation_versions_poll_execution_id ON reservation_versions (poll_execution_id);
CREATE INDEX ix_tickets_reservation_id ON tickets (reservation_id);
CREATE INDEX ix_schedule_guide_id ON schedule (guide_id);
CREATE INDEX ix_schedule_tour_id ON schedule (tour_id);
CREATE INDEX ix_schedule_event_start ON schedule (event_start_datetime);
CREATE INDEX ix_notifications_schedule_id ON notifications (schedule_id);
CREATE INDEX ix_notifications_guide_id ON notifications (guide_id);
CREATE INDEX ix_availability_patterns_guide_id ON availability_patterns (guide_id);
CREATE INDEX ix_availability_slots_pattern_id ON availability_slots (pattern_id);
CREATE INDEX ix_availability_exceptions_pattern_id ON availability_exceptions (pattern_id);
CREATE INDEX ix_sync_logs_poll_execution_id ON sync_logs (poll_execution_id);
CREATE INDEX ix_surveys_customer_id ON surveys (customer_id);
CREATE INDEX ix_surveys_guide_id ON surveys (guide_id);
CREATE INDEX ix_surveys_reservation_id ON surveys (reservation_id);
CREATE INDEX ix_tour_assignment_logs_schedule_id ON tour_assignment_logs (schedule_id);
CREATE INDEX ix_tour_assignment_logs_guide_id ON tour_assignment_logs (guide_id);
```

## Tables

| Table | Purpose |
|-------|---------|
| customers | External customers upserted from Clorian `clientId` |
| tours | Tour products mapped from Clorian `productId` |
| languages | Reference table of supported languages |
| users | Internal app users (staff, admins) |
| guides | Guide profiles with rating and active status |
| availability_patterns | Recurring availability template per guide |
| availability_slots | Weekly recurring time slots within a pattern |
| availability_exceptions | One-off overrides (holidays, sick days) |
| guide_languages | Junction: which languages a guide speaks |
| guide_tour_types | Junction: which tours a guide can lead |
| poll_execution | Tracks each Clorian polling cycle |
| sync_logs | Aggregated metrics per sync run |
| schedule | Groups reservations by tour + language + timeslot |
| reservations | Core bookable unit mapped from Clorian Reservation |
| reservation_versions | Immutable snapshot per ingestion cycle |
| tickets | Individual attendees within a reservation |
| surveys | Post-tour customer feedback |
| notifications | Portal and email notifications |
| tour_assignment_logs | Audit trail for guide assignments |

**Total: 19 tables + `alembic_version` (auto-managed) = 20 user tables.**

> Note: `guide_languages` and `guide_tour_types` are junction tables with composite primary keys and no surrogate `id` column.

## Relationships

| Parent | Child | FK Column | Cardinality |
|--------|-------|-----------|-------------|
| customers | reservations | customer_id | 1:N |
| tours | reservations | tour_id | 1:N |
| schedule | reservations | schedule_id | 1:N (nullable) |
| reservations | reservation_versions | reservation_id | 1:N |
| poll_execution | reservation_versions | poll_execution_id | 1:N |
| reservations | tickets | reservation_id | 1:N |
| customers | surveys | customer_id | 1:N |
| guides | surveys | guide_id | 1:N |
| reservations | surveys | reservation_id | 1:N |
| guides | schedule | guide_id | 1:N (nullable) |
| tours | schedule | tour_id | 1:N |
| schedule | notifications | schedule_id | 1:N |
| guides | notifications | guide_id | 1:N (nullable) |
| users | notifications | user_id | 1:N (nullable) |
| guides | availability_patterns | guide_id | 1:N |
| availability_patterns | availability_slots | pattern_id | 1:N |
| availability_patterns | availability_exceptions | pattern_id | 1:N |
| guides | guide_languages | guide_id | N:M (junction) |
| languages | guide_languages | language_id | N:M (junction) |
| guides | guide_tour_types | guide_id | N:M (junction) |
| tours | guide_tour_types | tour_id | N:M (junction) |
| poll_execution | sync_logs | poll_execution_id | 1:N |
| schedule | tour_assignment_logs | schedule_id | 1:N |
| guides | tour_assignment_logs | guide_id | 1:N |

## Indexes

| Table | Index Name | Columns | Type |
|-------|-----------|---------|------|
| customers | customers_pkey | id | PK |
| customers | customers_clorian_client_id_key | clorian_client_id | UNIQUE |
| tours | tours_pkey | id | PK |
| tours | tours_clorian_product_id_key | clorian_product_id | UNIQUE |
| languages | languages_pkey | id | PK |
| languages | languages_code_key | code | UNIQUE |
| users | users_pkey | id | PK |
| users | users_username_key | username | UNIQUE |
| users | users_email_key | email | UNIQUE |
| guides | guides_pkey | id | PK |
| reservations | reservations_pkey | id | PK |
| reservations | reservations_clorian_reservation_id_key | clorian_reservation_id | UNIQUE |
| reservations | ix_reservations_customer_id | customer_id | INDEX |
| reservations | ix_reservations_tour_id | tour_id | INDEX |
| reservations | ix_reservations_schedule_id | schedule_id | INDEX |
| reservations | ix_reservations_status | status | INDEX |
| reservation_versions | ix_reservation_versions_reservation_id | reservation_id | INDEX |
| reservation_versions | ix_reservation_versions_poll_execution_id | poll_execution_id | INDEX |
| tickets | tickets_pkey | id | PK |
| tickets | tickets_clorian_ticket_id_key | clorian_ticket_id | UNIQUE |
| tickets | ix_tickets_reservation_id | reservation_id | INDEX |
| schedule | schedule_pkey | id | PK |
| schedule | ix_schedule_guide_id | guide_id | INDEX |
| schedule | ix_schedule_tour_id | tour_id | INDEX |
| schedule | ix_schedule_event_start | event_start_datetime | INDEX |
| notifications | ix_notifications_schedule_id | schedule_id | INDEX |
| notifications | ix_notifications_guide_id | guide_id | INDEX |
| availability_patterns | ix_availability_patterns_guide_id | guide_id | INDEX |
| availability_slots | ix_availability_slots_pattern_id | pattern_id | INDEX |
| availability_exceptions | ix_availability_exceptions_pattern_id | pattern_id | INDEX |
| sync_logs | ix_sync_logs_poll_execution_id | poll_execution_id | INDEX |
| surveys | ix_surveys_customer_id | customer_id | INDEX |
| surveys | ix_surveys_guide_id | guide_id | INDEX |
| surveys | ix_surveys_reservation_id | reservation_id | INDEX |
| tour_assignment_logs | ix_tour_assignment_logs_schedule_id | schedule_id | INDEX |
| tour_assignment_logs | ix_tour_assignment_logs_guide_id | guide_id | INDEX |
| guide_languages | guide_languages_pkey | (guide_id, language_id) | PK (composite) |
| guide_tour_types | guide_tour_types_pkey | (guide_id, tour_id) | PK (composite) |

## Migration Notes

- **Migration file:** `migrations/versions/0001_initial_schema.py`
- **Type:** Greenfield — no existing data, no backfill required
- **Run:** `alembic upgrade head`
- **Rollback:** `alembic downgrade base` (drops all tables in reverse FK order using `CASCADE`)
- **Source of truth:** [ERD v4.0](ERD.md)
- **ORM:** None — raw SQL only via `op.execute()`

## Changelog

| Version | Date       | Author          | Description |
|---------|------------|-----------------|-------------|
| 1.0     | 2026-03-04 | Evandro Maciel  | Initial 20-table schema from ERD v4.0 |
