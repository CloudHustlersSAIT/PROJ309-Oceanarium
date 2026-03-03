"""Tour service -- read-only queries for the tours table."""

from sqlalchemy import text


def list_tours(conn):
    """Return all tours ordered alphabetically by tour name.

    Args:
        conn: SQLAlchemy connection provided by the route via ``Depends(get_db)``.

    Returns:
        list[dict]: Each dict maps column name to value for one tour row.
    """
    result = conn.execute(text("SELECT * FROM tours ORDER BY tour_name"))
    columns = result.keys()
    rows = [dict(zip(columns, row)) for row in result.fetchall()]
    return rows
