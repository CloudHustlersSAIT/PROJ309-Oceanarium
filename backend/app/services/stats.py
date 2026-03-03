"""Stats service -- dashboard aggregation queries.

Computes today's key metrics: active tours, total customers,
cancellations, and average guide rating.
"""

from datetime import date

from sqlalchemy import text


def get_stats(conn):
    """Aggregate dashboard statistics for today's date.

    Runs three separate SQL queries against the bookings table to count
    active tours, sum ticket holders, and count cancellations.

    Args:
        conn: SQLAlchemy connection provided by the route via ``Depends(get_db)``.

    Returns:
        dict: Keys are ``toursToday``, ``customersToday``, ``cancellations``,
        and ``avgRating`` (placeholder, always ``"5.0"`` until ratings are implemented).
    """
    today = date.today()

    tours_result = conn.execute(
        text("""
            SELECT COUNT(*) as count 
            FROM bookings 
            WHERE date = :today AND status != 'cancelled'
        """),
        {"today": today},
    )
    tours_today = tours_result.scalar() or 0

    customers_result = conn.execute(
        text("""
            SELECT COALESCE(SUM(adult_tickets + child_tickets), 0) as total
            FROM bookings 
            WHERE date = :today AND status != 'cancelled'
        """),
        {"today": today},
    )
    customers_today = customers_result.scalar() or 0

    cancellations_result = conn.execute(
        text("""
            SELECT COUNT(*) as count
            FROM bookings 
            WHERE date = :today AND status = 'cancelled'
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
