from datetime import date

from sqlalchemy import text

from .exceptions import ValidationError


def list_schedules(conn, start_date: date | None = None, end_date: date | None = None, status: str | None = None):
    if start_date and end_date and start_date > end_date:
        raise ValidationError("start_date cannot be after end_date")

    normalized_status = status.strip() if status else None
    if normalized_status == "":
        normalized_status = None

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
                (:start_date IS NULL OR s.event_end_datetime >= :start_date::date)
                AND (:end_date IS NULL OR s.event_start_datetime < (:end_date::date + INTERVAL '1 day'))
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
        )
        ,
        {
            "start_date": start_date,
            "end_date": end_date,
            "status": normalized_status,
        },
    )

    columns = result.keys()
    rows = [dict(zip(columns, row)) for row in result.fetchall()]
    return rows