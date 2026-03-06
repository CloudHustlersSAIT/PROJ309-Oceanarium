from sqlalchemy import text


def create_issue(conn, data):
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
