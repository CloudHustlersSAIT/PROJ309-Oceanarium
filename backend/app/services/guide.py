"""Guide service -- read-only queries for the guides table."""

from sqlalchemy import text


def list_guides(conn):
    """Return all guides ordered alphabetically by name.

    Args:
        conn: SQLAlchemy connection provided by the route via ``Depends(get_db)``.

    Returns:
        list[dict]: Each dict maps column name to value for one guide row.
    """
    result = conn.execute(text("SELECT * FROM guides ORDER BY name"))
    columns = result.keys()
    rows = [dict(zip(columns, row)) for row in result.fetchall()]
    return rows
