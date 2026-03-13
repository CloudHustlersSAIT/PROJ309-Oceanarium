from sqlalchemy import text


def list_languages(conn):
    result = conn.execute(
        text(
            """
            SELECT id, code, name
            FROM languages
            ORDER BY name
            """
        )
    )
    columns = result.keys()
    return [dict(zip(columns, row)) for row in result.fetchall()]
