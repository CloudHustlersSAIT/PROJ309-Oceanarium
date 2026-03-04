"""Initial schema — 20 tables from ERD v4.0

Revision ID: 0001
Revises:
Create Date: 2026-03-04
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Phase A: Independent tables (no FKs) ──

    op.execute("""
        CREATE TABLE customers (
            id              SERIAL PRIMARY KEY,
            clorian_client_id INTEGER NOT NULL UNIQUE,
            first_name      VARCHAR(255) NOT NULL,
            last_name       VARCHAR(255) NOT NULL,
            email           VARCHAR(255)
        );
    """)

    op.execute("""
        CREATE TABLE tours (
            id                SERIAL PRIMARY KEY,
            clorian_product_id INTEGER NOT NULL UNIQUE,
            name              VARCHAR(255) NOT NULL,
            description       TEXT,
            duration          INTEGER
        );
    """)

    op.execute("""
        CREATE TABLE languages (
            id   SERIAL PRIMARY KEY,
            code VARCHAR(10) NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL
        );
    """)

    op.execute("""
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
    """)

    op.execute("""
        CREATE TABLE guides (
            id           SERIAL PRIMARY KEY,
            first_name   VARCHAR(255) NOT NULL,
            last_name    VARCHAR(255) NOT NULL,
            email        VARCHAR(255),
            phone        VARCHAR(50),
            guide_rating DECIMAL(3,2),
            is_active    BOOLEAN NOT NULL DEFAULT TRUE
        );
    """)

    # ── Phase B: Tables with single FK to Phase A ──

    op.execute("""
        CREATE TABLE availability_patterns (
            id       SERIAL PRIMARY KEY,
            guide_id INTEGER NOT NULL REFERENCES guides(id),
            timezone VARCHAR(100) NOT NULL
        );
    """)

    op.execute("""
        CREATE TABLE poll_execution (
            id           SERIAL PRIMARY KEY,
            window_start TIMESTAMPTZ NOT NULL,
            window_end   TIMESTAMPTZ NOT NULL,
            executed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            status       VARCHAR(50) NOT NULL
        );
    """)

    # ── Phase C: Tables with FKs to Phase A+B ──

    op.execute("""
        CREATE TABLE availability_slots (
            id          SERIAL PRIMARY KEY,
            pattern_id  INTEGER NOT NULL REFERENCES availability_patterns(id),
            day_of_week VARCHAR(20) NOT NULL,
            start_time  TIME NOT NULL,
            end_time    TIME NOT NULL
        );
    """)

    op.execute("""
        CREATE TABLE availability_exceptions (
            id         SERIAL PRIMARY KEY,
            pattern_id INTEGER NOT NULL REFERENCES availability_patterns(id),
            date       DATE NOT NULL,
            type       VARCHAR(50) NOT NULL,
            reason     VARCHAR(255)
        );
    """)

    op.execute("""
        CREATE TABLE guide_languages (
            guide_id    INTEGER NOT NULL REFERENCES guides(id),
            language_id INTEGER NOT NULL REFERENCES languages(id),
            PRIMARY KEY (guide_id, language_id)
        );
    """)

    op.execute("""
        CREATE TABLE guide_tour_types (
            guide_id INTEGER NOT NULL REFERENCES guides(id),
            tour_id  INTEGER NOT NULL REFERENCES tours(id),
            PRIMARY KEY (guide_id, tour_id)
        );
    """)

    op.execute("""
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
    """)

    op.execute("""
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
    """)

    # ── Phase D: Tables with deeper FK chains ──

    op.execute("""
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
    """)

    op.execute("""
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
    """)

    op.execute("""
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
    """)

    op.execute("""
        CREATE TABLE surveys (
            id             SERIAL PRIMARY KEY,
            customer_id    INTEGER NOT NULL REFERENCES customers(id),
            guide_id       INTEGER NOT NULL REFERENCES guides(id),
            reservation_id INTEGER NOT NULL REFERENCES reservations(id),
            comment        TEXT,
            rating         INTEGER NOT NULL
        );
    """)

    op.execute("""
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
    """)

    op.execute("""
        CREATE TABLE tour_assignment_logs (
            id              SERIAL PRIMARY KEY,
            schedule_id     INTEGER NOT NULL REFERENCES schedule(id),
            guide_id        INTEGER NOT NULL REFERENCES guides(id),
            assigned_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            assigned_by     VARCHAR(255) NOT NULL,
            assignment_type VARCHAR(50) NOT NULL,
            action          VARCHAR(50) NOT NULL
        );
    """)

    # ── Query-path indexes ──

    op.execute("CREATE INDEX ix_reservations_customer_id ON reservations (customer_id);")
    op.execute("CREATE INDEX ix_reservations_tour_id ON reservations (tour_id);")
    op.execute("CREATE INDEX ix_reservations_schedule_id ON reservations (schedule_id);")
    op.execute("CREATE INDEX ix_reservations_status ON reservations (status);")
    op.execute("CREATE INDEX ix_reservation_versions_reservation_id ON reservation_versions (reservation_id);")
    op.execute("CREATE INDEX ix_reservation_versions_poll_execution_id ON reservation_versions (poll_execution_id);")
    op.execute("CREATE INDEX ix_tickets_reservation_id ON tickets (reservation_id);")
    op.execute("CREATE INDEX ix_schedule_guide_id ON schedule (guide_id);")
    op.execute("CREATE INDEX ix_schedule_tour_id ON schedule (tour_id);")
    op.execute("CREATE INDEX ix_schedule_event_start ON schedule (event_start_datetime);")
    op.execute("CREATE INDEX ix_notifications_schedule_id ON notifications (schedule_id);")
    op.execute("CREATE INDEX ix_notifications_guide_id ON notifications (guide_id);")
    op.execute("CREATE INDEX ix_availability_patterns_guide_id ON availability_patterns (guide_id);")
    op.execute("CREATE INDEX ix_availability_slots_pattern_id ON availability_slots (pattern_id);")
    op.execute("CREATE INDEX ix_availability_exceptions_pattern_id ON availability_exceptions (pattern_id);")
    op.execute("CREATE INDEX ix_sync_logs_poll_execution_id ON sync_logs (poll_execution_id);")
    op.execute("CREATE INDEX ix_surveys_customer_id ON surveys (customer_id);")
    op.execute("CREATE INDEX ix_surveys_guide_id ON surveys (guide_id);")
    op.execute("CREATE INDEX ix_surveys_reservation_id ON surveys (reservation_id);")
    op.execute("CREATE INDEX ix_tour_assignment_logs_schedule_id ON tour_assignment_logs (schedule_id);")
    op.execute("CREATE INDEX ix_tour_assignment_logs_guide_id ON tour_assignment_logs (guide_id);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS tour_assignment_logs CASCADE;")
    op.execute("DROP TABLE IF EXISTS notifications CASCADE;")
    op.execute("DROP TABLE IF EXISTS surveys CASCADE;")
    op.execute("DROP TABLE IF EXISTS tickets CASCADE;")
    op.execute("DROP TABLE IF EXISTS reservation_versions CASCADE;")
    op.execute("DROP TABLE IF EXISTS reservations CASCADE;")
    op.execute("DROP TABLE IF EXISTS schedule CASCADE;")
    op.execute("DROP TABLE IF EXISTS sync_logs CASCADE;")
    op.execute("DROP TABLE IF EXISTS guide_tour_types CASCADE;")
    op.execute("DROP TABLE IF EXISTS guide_languages CASCADE;")
    op.execute("DROP TABLE IF EXISTS availability_exceptions CASCADE;")
    op.execute("DROP TABLE IF EXISTS availability_slots CASCADE;")
    op.execute("DROP TABLE IF EXISTS poll_execution CASCADE;")
    op.execute("DROP TABLE IF EXISTS availability_patterns CASCADE;")
    op.execute("DROP TABLE IF EXISTS guides CASCADE;")
    op.execute("DROP TABLE IF EXISTS users CASCADE;")
    op.execute("DROP TABLE IF EXISTS languages CASCADE;")
    op.execute("DROP TABLE IF EXISTS tours CASCADE;")
    op.execute("DROP TABLE IF EXISTS customers CASCADE;")
