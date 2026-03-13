from sqlalchemy import text

from .exceptions import ValidationError


def list_guides(conn):
    result = conn.execute(text("SELECT * FROM guides ORDER BY first_name"))
    columns = result.keys()
    rows = [dict(zip(columns, row)) for row in result.fetchall()]
    return rows


def create_guide(conn, first_name: str, last_name: str, email: str):
    normalized_first_name = first_name.strip()
    normalized_last_name = last_name.strip()
    normalized_email = email.strip()

    if not normalized_first_name:
        raise ValidationError("first_name is required")
    if not normalized_last_name:
        raise ValidationError("last_name is required")
    if not normalized_email:
        raise ValidationError("email is required")

    result = conn.execute(
        text(
            """
            INSERT INTO guides (first_name, last_name, email)
            VALUES (:first_name, :last_name, :email)
            RETURNING id, first_name, last_name, email
            """
        ),
        {
            "first_name": normalized_first_name,
            "last_name": normalized_last_name,
            "email": normalized_email,
        },
    )
    conn.commit()

    row = result.fetchone()
    columns = result.keys()
    return dict(zip(columns, row))


def update_guide(conn, guide_id: int, fields: dict):
    if not fields:
        return None

    normalized_fields = fields.copy()
    if "email" in normalized_fields:
        normalized_fields["email"] = normalized_fields["email"].strip()
        if not normalized_fields["email"]:
            raise ValidationError("email cannot be empty")

    if "first_name" in normalized_fields:
        normalized_fields["first_name"] = normalized_fields["first_name"].strip()
        if not normalized_fields["first_name"]:
            raise ValidationError("first_name cannot be empty")

    if "last_name" in normalized_fields:
        normalized_fields["last_name"] = normalized_fields["last_name"].strip()
        if not normalized_fields["last_name"]:
            raise ValidationError("last_name cannot be empty")

    set_clause = ", ".join(f"{key} = :{key}" for key in normalized_fields)
    params = {"guide_id": guide_id, **normalized_fields}

    result = conn.execute(
        text(
            f"""
            UPDATE guides
            SET {set_clause}
            WHERE id = :guide_id
            RETURNING id, first_name, last_name, email
            """
        ),
        params,
    )
    conn.commit()

    row = result.fetchone()
    if row is None:
        return None
    columns = result.keys()
    return dict(zip(columns, row))
