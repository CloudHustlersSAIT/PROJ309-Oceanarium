from sqlalchemy import text


def list_customers(conn):
    result = conn.execute(
        text("""
            SELECT
                c.clorian_client_id,
                c.first_name || ' ' || c.last_name AS full_name,
                c.email,
                COUNT(r.id)                                     AS total_visits,
                CAST(MIN(r.event_start_datetime) AS date)       AS first_tour_date
            FROM customers c
            LEFT JOIN reservations r
                ON r.customer_id = c.id
               AND r.status != 'CANCELLED'
            GROUP BY c.clorian_client_id, c.first_name, c.last_name, c.email
            ORDER BY c.last_name, c.first_name
        """)
    )
    columns = result.keys()
    return [dict(zip(columns, row)) for row in result.fetchall()]


def update_customer(conn, customer_id: str, fields: dict):
    if not fields:
        return None

    set_clause = ", ".join(f"{key} = :{key}" for key in fields)
    params = {"customer_id": customer_id, **fields}

    result = conn.execute(
        text(f"""
            UPDATE customers
            SET {set_clause}
            WHERE clorian_client_id = :customer_id
            RETURNING clorian_client_id, first_name, last_name, email
        """),
        params,
    )
    conn.commit()

    row = result.fetchone()
    if row is None:
        return None
    columns = result.keys()
    return dict(zip(columns, row))
