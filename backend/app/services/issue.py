"""Issue service -- create operations for the issues table."""

from sqlalchemy import text


def create_issue(conn, data):
    """Insert a new issue record and return the created row.

    Args:
        conn: SQLAlchemy connection provided by the route via ``Depends(get_db)``.
        data: Pydantic model with a ``description`` field.

    Returns:
        dict: The newly created issue row as a column-name-to-value mapping.
    """
    result = conn.execute(
        text("""
            INSERT INTO issues (description)
            VALUES (:description)
            RETURNING *
        """),
        {"description": data.description},
    )
    conn.commit()
    columns = result.keys()
    row = result.fetchone()
    return dict(zip(columns, row))
