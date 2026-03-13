from sqlalchemy import text

from .exceptions import NotFoundError, ValidationError


def resolve_authenticated_user(conn, decoded_user: dict) -> dict:
    """
    Resolves the authenticated Firebase user into an application role.

    Resolution strategy:
    1. If email exists in users table with role='admin' and is_active=true -> admin
    2. Else if email exists in users table with role='guide' and is_active=true -> guide
    3. Else if email exists in guides table with is_active=true -> guide
    4. Else -> unauthorized / not mapped
    """
    email = str(decoded_user.get("email", "")).strip().lower()
    uid = decoded_user.get("uid")

    if not email:
        raise ValidationError("Decoded Firebase token must contain 'email' claim")

    user_row = conn.execute(
        text(
            """
        SELECT id, email, full_name, role, is_active
        FROM users
        WHERE LOWER(email) = :email
        LIMIT 1
        """
        ),
        {"email": email},
    ).fetchone()

    if user_row:
        normalized_role = str(user_row.role).strip().lower()

        if not user_row.is_active:
            raise ValidationError("User account is inactive")

        if normalized_role == "admin":
            return {
                "uid": uid,
                "email": email,
                "role": "admin",
                "user_id": user_row.id,
                "guide_id": None,
            }

        if normalized_role == "guide":
            full_name = str(user_row.full_name or "").strip()
            name_parts = full_name.split(None, 1) if full_name else []
            first_name = name_parts[0] if name_parts else None
            last_name = name_parts[1] if len(name_parts) > 1 else None

            return {
                "uid": uid,
                "email": email,
                "role": "guide",
                "user_id": user_row.id,
                "guide_id": user_row.id,
                "first_name": first_name,
                "last_name": last_name,
            }

    # If user is not admin, check guides table for guide role
    guide_row = conn.execute(
        text(
            """
            SELECT id, first_name, last_name, email, is_active
            FROM guides
            WHERE LOWER(email) = :email
              AND is_active = true
            LIMIT 1
            """
        ),
        {"email": email},
    ).fetchone()

    if guide_row:
        return {
            "uid": uid,
            "email": email,
            "role": "guide",
            "user_id": None,
            "guide_id": guide_row.id,
            "first_name": guide_row.first_name,
            "last_name": guide_row.last_name,
        }

    raise NotFoundError("Authenticated user is not mapped to an application role")
