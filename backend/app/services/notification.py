"""Notification service -- read-only queries for the notifications table."""

from sqlalchemy import text


def list_notifications(conn):
    """Return the 10 most recent notifications, newest first.

    Args:
        conn: SQLAlchemy connection provided by the route via ``Depends(get_db)``.

    Returns:
        list[dict]: Each dict maps column name to value for one notification row.
    """
    result = conn.execute(
        text("SELECT * FROM notifications ORDER BY created_at DESC LIMIT 10")
    )
    columns = result.keys()
    rows = [dict(zip(columns, row)) for row in result.fetchall()]
    return rows
