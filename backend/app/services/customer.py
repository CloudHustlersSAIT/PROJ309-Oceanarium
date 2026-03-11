from sqlalchemy import text


def list_customers(conn):
    result = conn.execute(
        text("""
            SELECT
                c.id,
                c.first_name || ' ' || c.last_name AS full_name,
                c.email,
                COUNT(r.id)                                     AS total_visits,
                CAST(MIN(r.event_start_datetime) AS date)       AS first_tour_date
            FROM customers c
            LEFT JOIN reservations r
                ON r.customer_id = c.id
               AND r.status != 'CANCELLED'
            GROUP BY c.id, c.first_name, c.last_name, c.email
            ORDER BY c.last_name, c.first_name
        """)
    )
    columns = result.keys()
    return [dict(zip(columns, row)) for row in result.fetchall()]
