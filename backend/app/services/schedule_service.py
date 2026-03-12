from datetime import timezone

from sqlalchemy import text


def get_or_create_schedule(
    conn,
    tour_id: int,
    language_code: str,
    event_start_datetime,
    event_end_datetime,
):
    """
    Return schedule id for the given (tour_id, language_code, event_start_datetime).
    If no such schedule exists, insert one with guide_id=NULL and status='CONFIRMED', then return its id.
    """
    # Normalize naive datetimes to UTC for consistent matching and insert.
    start_dt = event_start_datetime
    end_dt = event_end_datetime
    if start_dt is not None and getattr(start_dt, "tzinfo", None) is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    if end_dt is not None and getattr(end_dt, "tzinfo", None) is None:
        end_dt = end_dt.replace(tzinfo=timezone.utc)

    # Check if a schedule already exists.
    existing = conn.execute(
        text("""
            SELECT id
            FROM schedule
            WHERE tour_id = :tour_id
              AND language_code = :language_code
              AND event_start_datetime = :event_start_datetime
        """),
        {
            "tour_id": tour_id,
            "language_code": language_code,
            "event_start_datetime": start_dt,
        },
    ).fetchone()

    if existing:
        return existing[0]

    # Insert new schedule and return its id.
    new_id = conn.execute(
        text("""
            INSERT INTO schedule (
                guide_id,
                tour_id,
                language_code,
                event_start_datetime,
                event_end_datetime,
                status
            )
            VALUES (
                NULL,
                :tour_id,
                :language_code,
                :event_start_datetime,
                :event_end_datetime,
                'CONFIRMED'
            )
            RETURNING id
        """),
        {
            "tour_id": tour_id,
            "language_code": language_code,
            "event_start_datetime": start_dt,
            "event_end_datetime": end_dt,
        },
    ).scalar_one()

    return new_id
