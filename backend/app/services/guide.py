from sqlalchemy import text


def list_guides(conn):
    result = conn.execute(text("SELECT * FROM guides ORDER BY first_name"))
    columns = result.keys()
    rows = [dict(zip(columns, row)) for row in result.fetchall()]
    return rows
