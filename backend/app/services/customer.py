from typing import Optional

from sqlalchemy import text

from .exceptions import ConflictError, ValidationError


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


def _generate_next_manual_client_id(conn) -> str:
    max_result = conn.execute(
        text(
            """
            SELECT COALESCE(MAX(CAST(SUBSTRING(clorian_client_id FROM 8 FOR 6) AS INTEGER)), 0)
            FROM customers
            WHERE clorian_client_id LIKE 'MANUAL-%'
              AND LENGTH(clorian_client_id) = 13
              AND SUBSTRING(clorian_client_id FROM 8 FOR 6) ~ '^[0-9]{6}$'
            """
        )
    )
    current_max = max_result.scalar() or 0

    for next_value in range(current_max + 1, 1_000_000):
        candidate = f"MANUAL-{next_value:06d}"
        exists = conn.execute(
            text(
                """
                SELECT 1
                FROM customers
                WHERE clorian_client_id = :clorian_client_id
                """
            ),
            {"clorian_client_id": candidate},
        ).fetchone()
        if not exists:
            return candidate

    raise ValidationError("Manual customer id sequence exhausted")


def create_customer(
    conn,
    first_name: str,
    last_name: str,
    email: str,
    clorian_client_id: Optional[str] = None,
):
    normalized_first_name = first_name.strip()
    normalized_last_name = last_name.strip()
    normalized_email = email.strip()

    if not normalized_first_name:
        raise ValidationError("first_name is required")
    if not normalized_last_name:
        raise ValidationError("last_name is required")
    if not normalized_email:
        raise ValidationError("email is required")

    final_clorian_client_id = (clorian_client_id or "").strip()
    if not final_clorian_client_id:
        final_clorian_client_id = _generate_next_manual_client_id(conn)

    existing = conn.execute(
        text(
            """
            SELECT 1
            FROM customers
            WHERE clorian_client_id = :clorian_client_id
            """
        ),
        {"clorian_client_id": final_clorian_client_id},
    ).fetchone()
    if existing:
        raise ConflictError("Customer with this clorian_client_id already exists")

    result = conn.execute(
        text(
            """
            INSERT INTO customers (clorian_client_id, first_name, last_name, email)
            VALUES (:clorian_client_id, :first_name, :last_name, :email)
            RETURNING clorian_client_id, first_name, last_name, email
            """
        ),
        {
            "clorian_client_id": final_clorian_client_id,
            "first_name": normalized_first_name,
            "last_name": normalized_last_name,
            "email": normalized_email,
        },
    )
    conn.commit()

    row = result.fetchone()
    columns = result.keys()
    return dict(zip(columns, row))


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
