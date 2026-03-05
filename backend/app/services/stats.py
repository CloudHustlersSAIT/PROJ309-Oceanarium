from datetime import date

from sqlalchemy import text


def get_stats(conn):
    today = date.today()

    tours_result = conn.execute(
        text("""
            SELECT COUNT(*) as count
            FROM reservations
            WHERE event_start_datetime::date = :today
              AND status != 'cancelled'
        """),
        {"today": today},
    )
    tours_today = tours_result.scalar() or 0

    customers_result = conn.execute(
        text("""
            SELECT COALESCE(SUM(current_ticket_num), 0) as total
            FROM reservations
            WHERE event_start_datetime::date = :today
              AND status != 'cancelled'
        """),
        {"today": today},
    )
    customers_today = customers_result.scalar() or 0

    cancellations_result = conn.execute(
        text("""
            SELECT COUNT(*) as count
            FROM reservations
            WHERE event_start_datetime::date = :today
              AND status = 'cancelled'
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
