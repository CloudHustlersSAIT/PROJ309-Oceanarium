from __future__ import annotations

from datetime import date, timezone

from sqlalchemy import text

from .exceptions import NotFoundError, ValidationError


def list_schedules(conn, start_date: date | None = None, end_date: date | None = None, status: str | None = None):
    # Guard against impossible range filters before querying.
    if start_date and end_date and start_date > end_date:
        raise ValidationError("start_date cannot be after end_date")

    normalized_status = status.strip() if status else None
    if normalized_status == "":
        normalized_status = None

    # The query returns schedule rows enriched with joined names and reservation counts.
    result = conn.execute(
        text(
            """
            SELECT
                s.id,
                s.guide_id,
                s.tour_id,
                s.language_code,
                s.event_start_datetime,
                s.event_end_datetime,
                s.status,
                s.created_at,
                t.name AS tour_name,
                CASE
                    WHEN g.id IS NULL THEN NULL
                    ELSE CONCAT(g.first_name, ' ', g.last_name)
                END AS guide_name,
                COUNT(r.id) AS reservation_count
            FROM schedule s
            INNER JOIN tours t ON t.id = s.tour_id
            LEFT JOIN guides g ON g.id = s.guide_id
            LEFT JOIN reservations r ON r.schedule_id = s.id
            WHERE
                (:start_date IS NULL OR s.event_end_datetime >= CAST(:start_date AS date))
                AND (:end_date IS NULL OR s.event_start_datetime < (CAST(:end_date AS date) + INTERVAL '1 day'))
                AND (:status IS NULL OR LOWER(s.status) = LOWER(:status))
            GROUP BY
                s.id,
                s.guide_id,
                s.tour_id,
                s.language_code,
                s.event_start_datetime,
                s.event_end_datetime,
                s.status,
                s.created_at,
                t.name,
                g.id,
                g.first_name,
                g.last_name
            ORDER BY s.event_start_datetime
            """
        ),
        {
            "start_date": start_date,
            "end_date": end_date,
            "status": normalized_status,
        },
    )

    columns = result.keys()
    rows = [dict(zip(columns, row)) for row in result.fetchall()]
    return rows


def create_schedule(conn, data):
    # Basic temporal validation to prevent inverted schedule windows.
    if data.event_end_datetime <= data.event_start_datetime:
        raise ValidationError("event_end_datetime must be after event_start_datetime")

    language_code = (data.language_code or "").strip()
    if not language_code:
        raise ValidationError("language_code is required")

    if len(language_code) > 2:
        raise ValidationError("language_code must be at most 2 characters")

    status = (data.status or "CONFIRMED").strip().upper()
    if not status:
        raise ValidationError("status cannot be empty")

    # Normalize naive datetimes to UTC to keep inserts consistent.
    start_dt = data.event_start_datetime
    end_dt = data.event_end_datetime
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=timezone.utc)

    # Validate referenced catalog entities before insert for clearer API errors.
    tour = conn.execute(
        text(
            """
            SELECT id
            FROM tours
            WHERE id = :tour_id
            """
        ),
        {"tour_id": data.tour_id},
    ).fetchone()
    if not tour:
        raise NotFoundError("Tour not found")

    language = conn.execute(
        text(
            """
            SELECT code
            FROM languages
            WHERE LOWER(code) = LOWER(:language_code)
            """
        ),
        {"language_code": language_code},
    ).fetchone()
    if not language:
        raise ValidationError("language_code not found in languages table")

    # Persist the canonical code as stored in the languages catalog.
    language_code = language.code

    # guide_id is optional by design; validate only when supplied.
    guide_id = data.guide_id
    if guide_id is not None:
        guide = conn.execute(
            text(
                """
                SELECT id
                FROM guides
                WHERE id = :guide_id
                """
            ),
            {"guide_id": guide_id},
        ).fetchone()
        if not guide:
            raise NotFoundError("Guide not found")

    result = conn.execute(
        text(
            """
            INSERT INTO schedule
            (guide_id, tour_id, language_code, event_start_datetime, event_end_datetime, status)
            VALUES
            (:guide_id, :tour_id, :language_code, :event_start_datetime, :event_end_datetime, :status)
            RETURNING *
            """
        ),
        {
            "guide_id": guide_id,
            "tour_id": data.tour_id,
            "language_code": language_code,
            "event_start_datetime": start_dt,
            "event_end_datetime": end_dt,
            "status": status,
        },
    )

    conn.commit()

    columns = result.keys()
    row = result.fetchone()
    return dict(zip(columns, row))
