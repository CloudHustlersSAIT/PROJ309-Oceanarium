from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import text


def get_stats(conn):
    today = date.today()

    tours_result = conn.execute(
        text("""
            SELECT COUNT(*) as count
            FROM reservations
            WHERE event_start_datetime::date = :today
              AND status != 'CANCELLED'
        """),
        {"today": today},
    )
    tours_today = tours_result.scalar() or 0

    customers_result = conn.execute(
        text("""
            SELECT COALESCE(SUM(current_ticket_num), 0) as total
            FROM reservations
            WHERE event_start_datetime::date = :today
              AND status != 'CANCELLED'
        """),
        {"today": today},
    )
    customers_today = customers_result.scalar() or 0

    cancellations_result = conn.execute(
        text("""
            SELECT COUNT(*) as count
            FROM reservations
            WHERE event_start_datetime::date = :today
              AND status = 'CANCELLED'
        """),
        {"today": today},
    )
    cancellations = cancellations_result.scalar() or 0

    avg_rating = 5.0

    return {
        "toursToday": int(tours_today),
        "customersToday": int(customers_today),
        "cancellations": int(cancellations),
        "avgRating": str(avg_rating),
    }


_VALID_PERIODS = {"all_time", "this_month", "this_week", "this_day"}


def _normalize_period(period: str | None) -> str:
    normalized = str(period or "all_time").strip().lower()
    if normalized not in _VALID_PERIODS:
        normalized = "all_time"
    return normalized


def _resolve_window(selected_date: date | None, period: str | None) -> tuple[date | None, date, str]:
    anchor_date = selected_date or date.today()
    normalized_period = _normalize_period(period)

    if normalized_period == "this_day":
        start_date = anchor_date
    elif normalized_period == "this_week":
        start_date = anchor_date - timedelta(days=anchor_date.weekday())
    elif normalized_period == "this_month":
        start_date = anchor_date.replace(day=1)
    else:
        start_date = None

    return start_date, anchor_date, normalized_period


def _to_float(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _to_int(value) -> int:
    return int(value or 0)


def get_admin_dashboard(conn, selected_date: date | None = None, period: str | None = None):
    start_date, end_date, normalized_period = _resolve_window(selected_date, period)

    kpi_row = conn.execute(
        text(
            """
            SELECT
                (
                    SELECT COUNT(*)
                    FROM schedule s
                    WHERE s.event_start_datetime::date <= :end_date
                      AND (:start_date IS NULL OR s.event_start_datetime::date >= :start_date)
                      AND UPPER(s.status) != 'CANCELLED'
                ) AS total_tours_conducted,
                (
                    SELECT COALESCE(SUM(r.current_ticket_num), 0)
                    FROM reservations r
                    WHERE r.event_start_datetime::date <= :end_date
                      AND (:start_date IS NULL OR r.event_start_datetime::date >= :start_date)
                      AND UPPER(r.status) != 'CANCELLED'
                ) AS total_visitors_served,
                (
                    SELECT ROUND(AVG(g.guide_rating), 2)
                    FROM guides g
                    WHERE g.guide_rating IS NOT NULL
                ) AS avg_guide_rating
            """
        ),
        {"start_date": start_date, "end_date": end_date},
    ).mappings().one()

    tours_per_year_rows = conn.execute(
        text(
            """
            SELECT
                EXTRACT(YEAR FROM s.event_start_datetime)::int AS year,
                COUNT(*)::int AS value
            FROM schedule s
            WHERE s.event_start_datetime::date <= :end_date
              AND (:start_date IS NULL OR s.event_start_datetime::date >= :start_date)
              AND UPPER(s.status) != 'CANCELLED'
            GROUP BY EXTRACT(YEAR FROM s.event_start_datetime)
            ORDER BY year ASC
            """
        ),
        {"start_date": start_date, "end_date": end_date},
    ).mappings().all()

    visitors_per_tour_rows = conn.execute(
        text(
            """
            SELECT
                t.name AS label,
                COALESCE(SUM(r.current_ticket_num), 0)::int AS value
            FROM reservations r
            JOIN tours t ON t.id = r.tour_id
            WHERE r.event_start_datetime::date <= :end_date
              AND (:start_date IS NULL OR r.event_start_datetime::date >= :start_date)
              AND UPPER(r.status) != 'CANCELLED'
            GROUP BY t.id, t.name
            ORDER BY value DESC, t.name ASC
            LIMIT 8
            """
        ),
        {"start_date": start_date, "end_date": end_date},
    ).mappings().all()

    tours_by_language_rows = conn.execute(
        text(
            """
            SELECT
                COALESCE(l.name, UPPER(s.language_code)) AS label,
                LOWER(s.language_code) AS code,
                COUNT(*)::int AS value
            FROM schedule s
            LEFT JOIN languages l ON LOWER(l.code) = LOWER(s.language_code)
            WHERE s.event_start_datetime::date <= :end_date
              AND (:start_date IS NULL OR s.event_start_datetime::date >= :start_date)
              AND UPPER(s.status) != 'CANCELLED'
            GROUP BY COALESCE(l.name, UPPER(s.language_code)), LOWER(s.language_code)
            ORDER BY value DESC, label ASC
            LIMIT 8
            """
        ),
        {"start_date": start_date, "end_date": end_date},
    ).mappings().all()

    bookings_vs_cancellations_rows = conn.execute(
        text(
            """
            WITH booking_counts AS (
                SELECT
                    DATE_TRUNC('month', r.created_at)::date AS month_start,
                    COUNT(*)::int AS bookings
                FROM reservations r
                WHERE r.created_at::date <= :end_date
                  AND (:start_date IS NULL OR r.created_at::date >= :start_date)
                GROUP BY DATE_TRUNC('month', r.created_at)
            ),
            cancellation_counts AS (
                SELECT
                    DATE_TRUNC('month', COALESCE(r.clorian_modified_at, r.created_at))::date AS month_start,
                    COUNT(*)::int AS cancellations
                FROM reservations r
                WHERE UPPER(r.status) = 'CANCELLED'
                  AND COALESCE(r.clorian_modified_at, r.created_at)::date <= :end_date
                  AND (
                      :start_date IS NULL
                      OR COALESCE(r.clorian_modified_at, r.created_at)::date >= :start_date
                  )
                GROUP BY DATE_TRUNC('month', COALESCE(r.clorian_modified_at, r.created_at))
            ),
            combined AS (
                SELECT
                    COALESCE(b.month_start, c.month_start) AS month_start,
                    COALESCE(b.bookings, 0) AS bookings,
                    COALESCE(c.cancellations, 0) AS cancellations
                FROM booking_counts b
                FULL OUTER JOIN cancellation_counts c ON c.month_start = b.month_start
            ),
            limited AS (
                SELECT *
                FROM combined
                ORDER BY month_start DESC
                LIMIT 12
            )
            SELECT
                TO_CHAR(month_start, 'Mon YYYY') AS month,
                bookings,
                cancellations
            FROM limited
            ORDER BY month_start ASC
            """
        ),
        {"start_date": start_date, "end_date": end_date},
    ).mappings().all()

    top_guides_rows = conn.execute(
        text(
            """
            SELECT
                CONCAT(g.first_name, ' ', g.last_name) AS name,
                COUNT(s.id)::int AS tours,
                ROUND(g.guide_rating, 2) AS rating
            FROM guides g
            LEFT JOIN schedule s
                ON s.guide_id = g.id
               AND s.event_start_datetime::date <= :end_date
               AND (:start_date IS NULL OR s.event_start_datetime::date >= :start_date)
               AND UPPER(s.status) != 'CANCELLED'
            WHERE g.guide_rating IS NOT NULL
            GROUP BY g.id, g.first_name, g.last_name, g.guide_rating
            ORDER BY rating DESC, tours DESC, name ASC
            LIMIT 5
            """
        ),
        {"start_date": start_date, "end_date": end_date},
    ).mappings().all()

    notes = [
        "Avg occupancy rate remains mocked because the current schema has no capacity field per schedule or tour.",
    ]
    if normalized_period == "all_time":
        notes.append(
            "Historical series may look sparse because operational data population only started recently."
        )

    return {
        "filters": {
            "selectedDate": end_date.isoformat(),
            "period": normalized_period,
            "startDate": start_date.isoformat() if start_date else None,
            "endDate": end_date.isoformat(),
        },
        "kpis": {
            "totalToursConducted": _to_int(kpi_row["total_tours_conducted"]),
            "totalVisitorsServed": _to_int(kpi_row["total_visitors_served"]),
            "avgOccupancyRate": None,
            "avgGuideRating": _to_float(kpi_row["avg_guide_rating"]),
        },
        "toursPerYear": [
            {"label": str(row["year"]), "value": _to_int(row["value"])}
            for row in tours_per_year_rows
        ],
        "visitorsPerTour": [
            {"label": row["label"], "value": _to_int(row["value"])}
            for row in visitors_per_tour_rows
        ],
        "toursByLanguage": [
            {
                "label": row["label"],
                "code": row["code"],
                "value": _to_int(row["value"]),
            }
            for row in tours_by_language_rows
        ],
        "bookingsVsCancellations": [
            {
                "month": row["month"],
                "bookings": _to_int(row["bookings"]),
                "cancellations": _to_int(row["cancellations"]),
            }
            for row in bookings_vs_cancellations_rows
        ],
        "topRatedGuides": [
            {
                "name": row["name"],
                "tours": _to_int(row["tours"]),
                "rating": _to_float(row["rating"]),
            }
            for row in top_guides_rows
        ],
        "meta": {
            "occupancyRateAvailable": False,
            "notes": notes,
        },
    }
