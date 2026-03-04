from sqlalchemy import text


def list_tours(conn):
    result = conn.execute(text("SELECT * FROM tours ORDER BY tour_name"))
    columns = result.keys()
    rows = [dict(zip(columns, row)) for row in result.fetchall()]
    return rows
