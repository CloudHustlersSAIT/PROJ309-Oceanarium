"""
Guide availability for the Guide Profile page.

Reads and updates availability_patterns and availability_slots only.
Does not modify scheduler, poller, or assignment logic.
"""

from __future__ import annotations

import re
from datetime import time

from sqlalchemy import text

from .exceptions import NotFoundError, ValidationError

# Full day names as used by scheduler: TO_CHAR(..., 'Day') yields trimmed "Monday", etc.
FULL_DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
DAY_ALIASES = {
    "mon": "Monday",
    "tue": "Tuesday",
    "wed": "Wednesday",
    "thu": "Thursday",
    "fri": "Friday",
    "sat": "Saturday",
    "sun": "Sunday",
}

DEFAULT_TIMEZONE = "UTC"

# Time string HH:MM or HH:MM:SS
TIME_PATTERN = re.compile(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$")


def _normalize_day(day: str) -> str:
    """Return full day name (e.g. Monday) for scheduler compatibility. Raises ValidationError if invalid."""
    if not day or not isinstance(day, str):
        raise ValidationError("day is required and must be a non-empty string")
    cleaned = day.strip()
    if not cleaned:
        raise ValidationError("day cannot be blank")
    lower = cleaned.lower()
    if lower in DAY_ALIASES:
        return DAY_ALIASES[lower]
    if cleaned in FULL_DAY_NAMES:
        return cleaned
    if lower in (d.lower() for d in FULL_DAY_NAMES):
        return next(d for d in FULL_DAY_NAMES if d.lower() == lower)
    raise ValidationError(f"Invalid day: {day!r}. Use full name (e.g. Monday) or short form (e.g. Mon).")


def _parse_time(s: str) -> time:
    """Parse 'HH:MM' or 'HH:MM:SS' to time. Raises ValidationError if invalid."""
    if not s or not isinstance(s, str):
        raise ValidationError("start and end times must be non-empty strings")
    m = TIME_PATTERN.match(s.strip())
    if not m:
        raise ValidationError(f"Invalid time format: {s!r}. Use HH:MM or HH:MM:SS (e.g. 09:00).")
    h, mm, ss = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
    if h < 0 or h > 23 or mm < 0 or mm > 59 or ss < 0 or ss > 59:
        raise ValidationError(f"Time out of range: {s!r}")
    return time(hour=h, minute=mm, second=ss)


def _time_to_str(t: time) -> str:
    """Format time as HH:MM for API response."""
    return t.strftime("%H:%M")


def get_guide_availability(conn, guide_id: int) -> dict:
    """
    Return the guide's availability for the profile page.
    Uses the first availability_pattern for the guide (by id); if none exists,
    returns default timezone and empty slots (no pattern created on read).
    """
    pattern_row = conn.execute(
        text(
            """
            SELECT id, timezone
            FROM availability_patterns
            WHERE guide_id = :guide_id
            ORDER BY id
            LIMIT 1
            """
        ),
        {"guide_id": guide_id},
    ).fetchone()

    if not pattern_row:
        return {"timezone": DEFAULT_TIMEZONE, "slots": []}

    pattern_id = pattern_row[0]
    timezone = pattern_row[1] or DEFAULT_TIMEZONE

    rows = conn.execute(
        text(
            """
            SELECT day_of_week, start_time, end_time
            FROM availability_slots
            WHERE pattern_id = :pattern_id
            ORDER BY
                CASE LOWER(day_of_week)
                    WHEN 'monday'    THEN 1
                    WHEN 'tuesday'   THEN 2
                    WHEN 'wednesday' THEN 3
                    WHEN 'thursday'  THEN 4
                    WHEN 'friday'    THEN 5
                    WHEN 'saturday'  THEN 6
                    WHEN 'sunday'    THEN 7
                    ELSE 8
                END,
                start_time
            """
        ),
        {"pattern_id": pattern_id},
    ).fetchall()

    slots = []
    for row in rows:
        start_t = row[1]
        end_t = row[2]
        slots.append(
            {
                "day": row[0],
                "start": _time_to_str(start_t) if hasattr(start_t, "strftime") else str(start_t)[:5],
                "end": _time_to_str(end_t) if hasattr(end_t, "strftime") else str(end_t)[:5],
            }
        )

    return {"timezone": timezone, "slots": slots}


def update_guide_availability(conn, guide_id: int, slots: list[dict]) -> None:
    """
    Replace the guide's availability slots with the given list.
    Uses a single pattern per guide (first by id); creates one with DEFAULT_TIMEZONE if missing.
    Runs in one transaction: caller must use a single connection and commit after.
    Validates: start < end, valid day names. Does not modify scheduler or any other logic.
    """
    # Ensure guide exists
    guide = conn.execute(
        text("SELECT id FROM guides WHERE id = :guide_id"),
        {"guide_id": guide_id},
    ).fetchone()
    if not guide:
        raise NotFoundError("Guide not found")

    # Validate and normalize slots
    normalized = []
    for i, slot in enumerate(slots):
        if not isinstance(slot, dict):
            raise ValidationError(f"Slot at index {i} must be an object with day, start, end")
        day = slot.get("day")
        start_s = slot.get("start")
        end_s = slot.get("end")
        day_full = _normalize_day(day)
        start_t = _parse_time(start_s)
        end_t = _parse_time(end_s)
        if start_t >= end_t:
            raise ValidationError(
                f"Slot {i + 1}: start time must be before end time (got start={start_s!r}, end={end_s!r})"
            )
        normalized.append(
            {
                "day_of_week": day_full,
                "start_time": start_t.strftime("%H:%M:%S"),
                "end_time": end_t.strftime("%H:%M:%S"),
            }
        )

    # Find or create pattern (one per guide)
    pattern_row = conn.execute(
        text(
            """
            SELECT id, timezone
            FROM availability_patterns
            WHERE guide_id = :guide_id
            ORDER BY id
            LIMIT 1
            """
        ),
        {"guide_id": guide_id},
    ).fetchone()

    if pattern_row:
        pattern_id = pattern_row[0]
    else:
        result = conn.execute(
            text(
                """
                INSERT INTO availability_patterns (guide_id, timezone)
                VALUES (:guide_id, :timezone)
                RETURNING id
                """
            ),
            {"guide_id": guide_id, "timezone": DEFAULT_TIMEZONE},
        )
        row = result.fetchone()
        pattern_id = row[0]

    # Replace slots in one go (delete then insert)
    conn.execute(
        text("DELETE FROM availability_slots WHERE pattern_id = :pattern_id"),
        {"pattern_id": pattern_id},
    )

    for s in normalized:
        conn.execute(
            text(
                """
                INSERT INTO availability_slots (pattern_id, day_of_week, start_time, end_time)
                VALUES (:pattern_id, :day_of_week, CAST(:start_time AS time), CAST(:end_time AS time))
                """
            ),
            {
                "pattern_id": pattern_id,
                "day_of_week": s["day_of_week"],
                "start_time": s["start_time"],
                "end_time": s["end_time"],
            },
        )

    conn.commit()
