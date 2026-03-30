from sqlalchemy import text

from .content_moderation import assert_text_is_safe
from .exceptions import ValidationError

VALID_DAYS_OF_WEEK = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
}


def _fetch_guide_profile(conn, guide_id: int):
    guide_row = conn.execute(
        text(
            """
            SELECT id, first_name, last_name, email, phone, guide_rating, is_active
            FROM guides
            WHERE id = :guide_id
            """
        ),
        {"guide_id": guide_id},
    ).fetchone()
    if not guide_row:
        return None

    guide = dict(guide_row._mapping)
    guide["full_name"] = f"{guide['first_name']} {guide['last_name']}"

    language_rows = conn.execute(
        text(
            """
            SELECT l.code
            FROM guide_languages gl
            JOIN languages l ON l.id = gl.language_id
            WHERE gl.guide_id = :guide_id
            ORDER BY l.code
            """
        ),
        {"guide_id": guide_id},
    ).fetchall()
    guide["language_codes"] = [row[0] for row in language_rows]

    expertise_rows = conn.execute(
        text(
            """
            SELECT gtt.tour_id
            FROM guide_tour_types gtt
            WHERE gtt.guide_id = :guide_id
            ORDER BY gtt.tour_id
            """
        ),
        {"guide_id": guide_id},
    ).fetchall()
    guide["expertise_tour_ids"] = [row[0] for row in expertise_rows]

    pattern_rows = conn.execute(
        text(
            """
            SELECT id, timezone
            FROM availability_patterns
            WHERE guide_id = :guide_id
            ORDER BY id
            """
        ),
        {"guide_id": guide_id},
    ).fetchall()

    availability_patterns = []
    for pattern in pattern_rows:
        slot_rows = conn.execute(
            text(
                """
                SELECT day_of_week, start_time, end_time
                FROM availability_slots
                WHERE pattern_id = :pattern_id
                ORDER BY id
                """
            ),
            {"pattern_id": pattern.id},
        ).fetchall()
        availability_patterns.append(
            {
                "id": pattern.id,
                "timezone": pattern.timezone,
                "slots": [
                    {
                        "day_of_week": slot.day_of_week,
                        "start_time": str(slot.start_time),
                        "end_time": str(slot.end_time),
                    }
                    for slot in slot_rows
                ],
            }
        )
    guide["availability_patterns"] = availability_patterns

    return guide


def _normalize_language_codes(language_codes: list[str]) -> list[str]:
    normalized_codes = []
    for code in language_codes:
        normalized = code.strip().lower()
        if not normalized:
            raise ValidationError("language_codes cannot contain empty values")
        normalized_codes.append(normalized)
    return sorted(set(normalized_codes))


def _replace_guide_languages(conn, guide_id: int, language_codes: list[str]) -> None:
    normalized_codes = _normalize_language_codes(language_codes)

    conn.execute(
        text("DELETE FROM guide_languages WHERE guide_id = :guide_id"),
        {"guide_id": guide_id},
    )

    if not normalized_codes:
        return

    rows = conn.execute(
        text(
            """
            SELECT id, LOWER(code) AS code
            FROM languages
            WHERE LOWER(code) = ANY(:codes)
            """
        ),
        {"codes": normalized_codes},
    ).fetchall()

    found_codes = {row.code for row in rows}
    missing = [code for code in normalized_codes if code not in found_codes]
    if missing:
        raise ValidationError(f"language_codes not found in languages table: {', '.join(missing)}")

    conn.execute(
        text(
            """
            INSERT INTO guide_languages (guide_id, language_id)
            VALUES (:guide_id, :language_id)
            """
        ),
        [{"guide_id": guide_id, "language_id": row.id} for row in rows],
    )


def _replace_guide_expertise(conn, guide_id: int, tour_ids: list[int]) -> None:
    unique_tour_ids = sorted(set(tour_ids))

    conn.execute(
        text("DELETE FROM guide_tour_types WHERE guide_id = :guide_id"),
        {"guide_id": guide_id},
    )

    if not unique_tour_ids:
        return

    rows = conn.execute(
        text(
            """
            SELECT id
            FROM tours
            WHERE id = ANY(:tour_ids)
            """
        ),
        {"tour_ids": unique_tour_ids},
    ).fetchall()

    found_ids = {row.id for row in rows}
    missing = [str(tour_id) for tour_id in unique_tour_ids if tour_id not in found_ids]
    if missing:
        raise ValidationError(f"expertise_tour_ids not found in tours table: {', '.join(missing)}")

    conn.execute(
        text(
            """
            INSERT INTO guide_tour_types (guide_id, tour_id)
            VALUES (:guide_id, :tour_id)
            """
        ),
        [{"guide_id": guide_id, "tour_id": tour_id} for tour_id in unique_tour_ids],
    )


def _validate_and_normalize_patterns(availability_patterns: list[dict]) -> list[dict]:
    normalized_patterns = []
    for pattern in availability_patterns:
        timezone_value = (pattern.get("timezone") or "").strip()
        if not timezone_value:
            raise ValidationError("availability pattern timezone is required")

        normalized_slots = []
        for slot in pattern.get("slots", []):
            day_value = (slot.get("day_of_week") or "").strip().lower()
            if day_value not in VALID_DAYS_OF_WEEK:
                raise ValidationError(f"Invalid day_of_week: {slot.get('day_of_week')}")

            start_time = slot.get("start_time")
            end_time = slot.get("end_time")
            if start_time is None or end_time is None:
                raise ValidationError("availability slot requires start_time and end_time")
            if start_time >= end_time:
                raise ValidationError("availability slot end_time must be after start_time")

            normalized_slots.append(
                {
                    "day_of_week": day_value.capitalize(),
                    "start_time": start_time,
                    "end_time": end_time,
                }
            )

        normalized_patterns.append(
            {
                "timezone": timezone_value,
                "slots": normalized_slots,
            }
        )

    return normalized_patterns


def _replace_guide_availability(conn, guide_id: int, availability_patterns: list[dict]) -> None:
    normalized_patterns = _validate_and_normalize_patterns(availability_patterns)

    conn.execute(
        text(
            """
            DELETE FROM availability_slots
            WHERE pattern_id IN (
                SELECT id
                FROM availability_patterns
                WHERE guide_id = :guide_id
            )
            """
        ),
        {"guide_id": guide_id},
    )
    conn.execute(
        text("DELETE FROM availability_patterns WHERE guide_id = :guide_id"),
        {"guide_id": guide_id},
    )

    for pattern in normalized_patterns:
        pattern_row = conn.execute(
            text(
                """
                INSERT INTO availability_patterns (guide_id, timezone)
                VALUES (:guide_id, :timezone)
                RETURNING id
                """
            ),
            {
                "guide_id": guide_id,
                "timezone": pattern["timezone"],
            },
        ).fetchone()

        if pattern["slots"]:
            conn.execute(
                text(
                    """
                    INSERT INTO availability_slots (pattern_id, day_of_week, start_time, end_time)
                    VALUES (:pattern_id, :day_of_week, :start_time, :end_time)
                    """
                ),
                [
                    {
                        "pattern_id": pattern_row.id,
                        "day_of_week": slot["day_of_week"],
                        "start_time": slot["start_time"],
                        "end_time": slot["end_time"],
                    }
                    for slot in pattern["slots"]
                ],
            )


def list_guides(conn):
    result = conn.execute(text("SELECT id FROM guides ORDER BY first_name, last_name, id"))
    guide_ids = [row[0] for row in result.fetchall()]
    return [_fetch_guide_profile(conn, guide_id) for guide_id in guide_ids]


def create_guide(
    conn,
    first_name: str,
    last_name: str,
    email: str,
    phone: str | None = None,
    language_codes: list[str] | None = None,
    expertise_tour_ids: list[int] | None = None,
    availability_patterns: list[dict] | None = None,
):
    normalized_first_name = first_name.strip()
    normalized_last_name = last_name.strip()
    normalized_email = email.strip()
    normalized_phone = phone.strip() if isinstance(phone, str) else None

    if not normalized_first_name:
        raise ValidationError("first_name is required")
    if not normalized_last_name:
        raise ValidationError("last_name is required")
    if not normalized_email:
        raise ValidationError("email is required")
    if normalized_phone is not None and normalized_phone and not normalized_phone.isdigit():
        raise ValidationError("phone must contain digits only")

    assert_text_is_safe(normalized_first_name, "first_name")
    assert_text_is_safe(normalized_last_name, "last_name")

    result = conn.execute(
        text(
            """
            INSERT INTO guides (first_name, last_name, email, phone)
            VALUES (:first_name, :last_name, :email, :phone)
            RETURNING id
            """
        ),
        {
            "first_name": normalized_first_name,
            "last_name": normalized_last_name,
            "email": normalized_email,
            "phone": normalized_phone,
        },
    )

    guide_id = result.fetchone().id

    _replace_guide_languages(conn, guide_id, language_codes or [])
    _replace_guide_expertise(conn, guide_id, expertise_tour_ids or [])
    _replace_guide_availability(conn, guide_id, availability_patterns or [])

    conn.commit()

    return _fetch_guide_profile(conn, guide_id)


def update_guide(conn, guide_id: int, fields: dict):
    if not fields:
        return None

    guide_exists = conn.execute(
        text("SELECT 1 FROM guides WHERE id = :guide_id"),
        {"guide_id": guide_id},
    ).fetchone()
    if not guide_exists:
        return None

    normalized_fields = fields.copy()
    language_codes = normalized_fields.pop("language_codes", None)
    expertise_tour_ids = normalized_fields.pop("expertise_tour_ids", None)
    availability_patterns = normalized_fields.pop("availability_patterns", None)

    if "email" in normalized_fields:
        normalized_fields["email"] = normalized_fields["email"].strip()
        if not normalized_fields["email"]:
            raise ValidationError("email cannot be empty")

    if "first_name" in normalized_fields:
        normalized_fields["first_name"] = normalized_fields["first_name"].strip()
        if not normalized_fields["first_name"]:
            raise ValidationError("first_name cannot be empty")
        assert_text_is_safe(normalized_fields["first_name"], "first_name")

    if "last_name" in normalized_fields:
        normalized_fields["last_name"] = normalized_fields["last_name"].strip()
        if not normalized_fields["last_name"]:
            raise ValidationError("last_name cannot be empty")
        assert_text_is_safe(normalized_fields["last_name"], "last_name")

    if "phone" in normalized_fields:
        phone_value = normalized_fields["phone"]
        if phone_value is None:
            normalized_fields["phone"] = None
        else:
            normalized_fields["phone"] = str(phone_value).strip()
            if normalized_fields["phone"] and not normalized_fields["phone"].isdigit():
                raise ValidationError("phone must contain digits only")

    if normalized_fields:
        set_clause = ", ".join(f"{key} = :{key}" for key in normalized_fields)
        params = {"guide_id": guide_id, **normalized_fields}

        conn.execute(
            text(
                f"""
                UPDATE guides
                SET {set_clause}
                WHERE id = :guide_id
                """
            ),
            params,
        )

    if language_codes is not None:
        _replace_guide_languages(conn, guide_id, language_codes)

    if expertise_tour_ids is not None:
        _replace_guide_expertise(conn, guide_id, expertise_tour_ids)

    if availability_patterns is not None:
        _replace_guide_availability(conn, guide_id, availability_patterns)

    conn.commit()

    return _fetch_guide_profile(conn, guide_id)


def soft_delete_guide(conn, guide_id: int):
    result = conn.execute(
        text(
            """
            UPDATE guides
            SET is_active = false
            WHERE id = :guide_id
            RETURNING id
            """
        ),
        {"guide_id": guide_id},
    ).fetchone()

    if not result:
        return None

    conn.commit()
    return _fetch_guide_profile(conn, guide_id)
