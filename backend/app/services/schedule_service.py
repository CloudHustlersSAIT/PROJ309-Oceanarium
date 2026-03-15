import logging

from sqlalchemy import text

logger = logging.getLogger(__name__)


def get_or_create_schedule(
    conn,
    tour_id: int,
    language_code: str,
    event_start_datetime,
    event_end_datetime,
    status: str = "CONFIRMED",
):
    """
    Returns an existing schedule_id if a matching schedule exists.
    Otherwise creates a new schedule and returns its id.

    Matching rules (per PM instructions):
        - tour_id
        - language_code
        - event_start_datetime

    Multiple reservations can share the same schedule.
    """

    language = (language_code or "").strip().lower()

    # Step 1 — Check if schedule already exists
    existing = conn.execute(
        text(
            """
            SELECT id
            FROM schedule
            WHERE tour_id = :tour_id
            AND LOWER(language_code) = LOWER(:language_code)
            AND event_start_datetime = :event_start
            AND status IN ('UNASSIGNED', 'ASSIGNED', 'CONFIRMED')
            LIMIT 1
            """
        ),
        {
            "tour_id": tour_id,
            "language_code": language,
            "event_start": event_start_datetime,
        },
    ).fetchone()

    if existing:
        return existing[0]

    # Step 2 — Create new schedule if none exists
    row = conn.execute(
        text(
            """
            INSERT INTO schedule
            (tour_id, language_code, event_start_datetime, event_end_datetime, status)
            VALUES
            (:tour_id, :language_code, :event_start, :event_end, :status)
            RETURNING id
            """
        ),
        {
            "tour_id": tour_id,
            "language_code": language,
            "event_start": event_start_datetime,
            "event_end": event_end_datetime,
            "status": status,
        },
    ).fetchone()

    return row[0]
