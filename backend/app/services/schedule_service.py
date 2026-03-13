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
) -> int:
    """
    Returns an existing schedule_id if a matching schedule exists,
    otherwise creates a new schedule and returns its id.

    Matching criteria:
        - tour_id
        - language_code
        - event_start_datetime

    This ensures multiple reservations can share the same schedule
    while preventing duplicate schedules from being created.
    """

    # Normalize language code for consistent comparison
    language = (language_code or "").strip().lower()

    # Step 1: Check if a matching schedule already exists
    existing = conn.execute(
        text(
            """
            SELECT id
            FROM schedule
            WHERE tour_id = :tour_id
              AND LOWER(language_code) = LOWER(:language_code)
              AND event_start_datetime = :event_start
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
