from sqlalchemy import text


def get_dashboard(conn, guide_id: int):

    next_tour_sql = text("""
        SELECT
            s.id,
            t.name AS tour_name,
            s.event_start_datetime,
            s.event_end_datetime,
            s.language_code
        FROM schedule s
        JOIN tours t ON t.id = s.tour_id
        WHERE s.guide_id = :guide_id
        AND s.event_start_datetime > NOW()
        ORDER BY s.event_start_datetime
        LIMIT 1
    """)

    next_tour = conn.execute(next_tour_sql, {"guide_id": guide_id}).mappings().first()

    week_count_sql = text("""
        SELECT COUNT(*) AS total
        FROM schedule
        WHERE guide_id = :guide_id
        AND event_start_datetime >= DATE_TRUNC('week', NOW())
    """)

    tours_week = conn.execute(week_count_sql, {"guide_id": guide_id}).scalar()

    pending_requests_sql = text("""
        SELECT COUNT(*) AS total
        FROM tour_assignment_logs tal
        WHERE tal.guide_id = :guide_id
        AND tal.action = 'SWAP_REQUEST'
        AND NOT EXISTS (
            SELECT 1
            FROM tour_assignment_logs resolved
            WHERE resolved.schedule_id = tal.schedule_id
              AND resolved.guide_id = tal.guide_id
              AND resolved.assignment_type = 'SWAP'
              AND resolved.action IN ('SWAP_ACCEPTED', 'SWAP_REJECTED')
              AND resolved.assigned_at >= tal.assigned_at
        )
    """)

    pending_requests = conn.execute(pending_requests_sql, {"guide_id": guide_id}).scalar()

    rating_sql = text("""
        SELECT guide_rating
        FROM guides
        WHERE id = :guide_id
    """)

    rating = conn.execute(rating_sql, {"guide_id": guide_id}).scalar()

    today_schedule_sql = text("""
        SELECT
            s.id,
            t.name,
            s.event_start_datetime,
            s.event_end_datetime,
            s.language_code,
            s.status
        FROM schedule s
        JOIN tours t ON t.id = s.tour_id
        WHERE s.guide_id = :guide_id
        AND DATE(s.event_start_datetime) = CURRENT_DATE
        ORDER BY s.event_start_datetime
    """)

    today_schedule = conn.execute(today_schedule_sql, {"guide_id": guide_id}).mappings().all()

    return {
        "next_tour": next_tour,
        "tours_this_week": tours_week,
        "pending_requests": pending_requests,
        "rating": rating,
        "today_schedule": today_schedule,
    }
