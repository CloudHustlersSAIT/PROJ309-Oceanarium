from sqlalchemy import text

from .exceptions import NotFoundError, ValidationError


def resolve_authenticated_user(conn, decoded_user: dict) -> dict:
    """
    Resolves the authenticated Firebase user into an application role.

    Resolution strategy:
    1. If email exists in users table with role='admin' and is_active=true -> admin
    2. Else if email exists in guides table with is_active=true -> guide
    3. Else -> unauthorized / not mapped
    """
    email = str(decoded_user.get("email", "")).strip().lower()
    uid = decoded_user.get("uid")

    if not email:
        raise ValidationError("Decoded Firebase token must contain 'email' claim")

    #Check users table for admin role
    admin_row = conn.execute(
    text(
        """
        SELECT id, email, role, is_active
        FROM users
        WHERE LOWER(email) = :email
        LIMIT 1
        """
        ),
        {"email": email},
    ).fetchone()
    
    if admin_row:
        # Confirm this row is actually an admin before applying the inactive-user check,
        # so a non-admin inactive row doesn't block guide resolution.
        if str(admin_row.role).strip().lower() == "admin":
            if not admin_row.is_active:
                raise ValidationError("User account is inactive")
            return {
                "uid": uid,
                "email": email,
                "role": "admin",
                "user_id": admin_row.id,
                "guide_id": None,
            }
        
    #If user is not admin, check guides table for guide role
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