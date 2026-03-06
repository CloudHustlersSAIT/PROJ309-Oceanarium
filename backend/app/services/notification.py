from sqlalchemy import text


def list_notifications(conn):
    result = conn.execute(
        text("SELECT * FROM notifications ORDER BY created_at DESC LIMIT 10")
    )
    columns = result.keys()
    rows = [dict(zip(columns, row)) for row in result.fetchall()]
    return rows
