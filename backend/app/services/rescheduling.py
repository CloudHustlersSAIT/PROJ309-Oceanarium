from __future__ import annotations

import logging

from sqlalchemy import text

from .exceptions import NotFoundError, UnassignableError
from .guide_assignment import auto_assign_guide

logger = logging.getLogger(__name__)


def find_matching_schedule(
    conn,
    tour_id: int,
    language_code: str,
    event_start_datetime,
) -> int | None:
    """FR-6: Find an active schedule matching tour + language + timeslot."""
    row = conn.execute(
        text(
            """
            SELECT id
            FROM schedule
            WHERE tour_id = :tour_id
              AND LOWER(language_code) = LOWER(:language_code)
              AND event_start_datetime = :event_start
              AND status IN ('UNASSIGNED', 'ASSIGNED', 'CONFIRMED')
            ORDER BY id
            LIMIT 1
            """
        ),
        {
            "tour_id": tour_id,
            "language_code": language_code,
            "event_start": event_start_datetime,
        },
    ).fetchone()
    return row[0] if row else None


def find_or_create_schedule(
    conn,
    tour_id: int,
    language_code: str,
    event_start_datetime,
    event_end_datetime,
) -> tuple[int, list[dict]]:
    """Find a matching schedule or create a new one and attempt guide assignment.

    Returns: (schedule_id, notification_events)
    """
    events = []
    schedule_id = find_matching_schedule(conn, tour_id, language_code, event_start_datetime)
    if schedule_id is not None:
        return schedule_id, events

    row = conn.execute(
        text(
            """
            INSERT INTO schedule
                (tour_id, language_code, event_start_datetime, event_end_datetime, status)
            VALUES
                (:tour_id, :language_code, :event_start, :event_end, 'UNASSIGNED')
            RETURNING id
            """
        ),
        {
            "tour_id": tour_id,
            "language_code": language_code,
            "event_start": event_start_datetime,
            "event_end": event_end_datetime,
        },
    ).fetchone()
    schedule_id = row[0]

    try:
        result = auto_assign_guide(conn, schedule_id, commit=False)
        # Extract notification event from result
        if "_notification_event" in result:
            events.append(result["_notification_event"])
    except UnassignableError as e:
        # Extract notification event from exception
        if hasattr(e, "notification_event"):
            events.append(e.notification_event)

    return schedule_id, events


def cleanup_empty_schedule(conn, schedule_id: int) -> list[dict]:
    """Cancel a schedule and unassign its guide if no active reservations remain.

    Returns: notification_events
    """
    events = []
    count = conn.execute(
        text(
            """
            SELECT COUNT(*)
            FROM reservations
            WHERE schedule_id = :schedule_id AND status != 'CANCELLED'
            """
        ),
        {"schedule_id": schedule_id},
    ).scalar_one()

    if count > 0:
        return events

    schedule = conn.execute(
        text("SELECT id, guide_id FROM schedule WHERE id = :id"),
        {"id": schedule_id},
    ).fetchone()
    if not schedule:
        return events

    old_guide_id = schedule[1]

    conn.execute(
        text("UPDATE schedule SET status = 'CANCELLED', guide_id = NULL WHERE id = :id"),
        {"id": schedule_id},
    )

    if old_guide_id is not None:
        conn.execute(
            text(
                """
                INSERT INTO tour_assignment_logs
                    (schedule_id, guide_id, assigned_by, assignment_type, action)
                VALUES
                    (:schedule_id, :guide_id, 'system', 'AUTO', 'UNASSIGNED')
                """
            ),
            {"schedule_id": schedule_id, "guide_id": old_guide_id},
        )
        events.append({
            "type": "GUIDE_UNASSIGNED",
            "schedule_id": schedule_id,
            "guide_id": old_guide_id,
            "reason": "Schedule cancelled (no remaining reservations)",
        })

    return events


def handle_reservation_change(
    conn,
    reservation_id: int,
    old_schedule_id: int | None,
    new_tour_id: int,
    new_language_code: str,
    new_event_start,
    new_event_end,
) -> list[dict]:
    """FR-1/FR-2/FR-3: Move a reservation whose tour, language, or time changed.

    Returns: notification_events
    """
    events = []
    conn.execute(
        text("UPDATE reservations SET schedule_id = NULL WHERE id = :id"),
        {"id": reservation_id},
    )

    new_schedule_id, schedule_events = find_or_create_schedule(
        conn, new_tour_id, new_language_code, new_event_start, new_event_end
    )
    events.extend(schedule_events)

    conn.execute(
        text("UPDATE reservations SET schedule_id = :sid WHERE id = :id"),
        {"sid": new_schedule_id, "id": reservation_id},
    )

    # Get guide info for notification
    new_schedule = conn.execute(
        text("SELECT guide_id FROM schedule WHERE id = :id"),
        {"id": new_schedule_id},
    ).fetchone()

    events.append({
        "type": "SCHEDULE_CHANGED",
        "schedule_id": new_schedule_id,
        "event_type": "RESERVATION_MOVED",
        "reason": (
            f"Reservation {reservation_id} moved to this schedule"
            + (f" from schedule {old_schedule_id}" if old_schedule_id else "")
        ),
        "affected_guide_id": new_schedule[0] if new_schedule and new_schedule[0] else None,
    })

    if old_schedule_id is not None:
        cleanup_events = cleanup_empty_schedule(conn, old_schedule_id)
        events.extend(cleanup_events)

    return events


def handle_reservation_cancellation(
    conn,
    reservation_id: int,
    old_schedule_id: int,
) -> list[dict]:
    """FR-4: Clean up after a reservation is cancelled.

    Returns: notification_events
    """
    events = []
    # Get guide info for notification
    schedule = conn.execute(
        text("SELECT guide_id FROM schedule WHERE id = :id"),
        {"id": old_schedule_id},
    ).fetchone()

    events.append({
        "type": "SCHEDULE_CHANGED",
        "schedule_id": old_schedule_id,
        "event_type": "RESERVATION_CANCELLED",
        "reason": f"Reservation {reservation_id} was cancelled and removed",
        "affected_guide_id": schedule[0] if schedule and schedule[0] else None,
    })

    cleanup_events = cleanup_empty_schedule(conn, old_schedule_id)
    events.extend(cleanup_events)

    return events


def handle_guide_cancellation(conn, schedule_id: int) -> dict:
    """FR-5: Unassign a guide and attempt to find a replacement.

    Returns: result dict with _notification_events list
    """
    events = []
    schedule = conn.execute(
        text(
            """
            SELECT id, guide_id, tour_id, language_code,
                   event_start_datetime, event_end_datetime, status
            FROM schedule WHERE id = :id
            """
        ),
        {"id": schedule_id},
    ).fetchone()
    if not schedule:
        raise NotFoundError("Schedule not found")

    sched = dict(schedule._mapping)
    old_guide_id = sched["guide_id"]
    if old_guide_id is None:
        return {
            "schedule_id": schedule_id,
            "status": sched["status"],
            "message": "No guide was assigned",
            "_notification_events": events,
        }

    conn.execute(
        text("UPDATE schedule SET guide_id = NULL, status = 'UNASSIGNED' WHERE id = :id"),
        {"id": schedule_id},
    )
    conn.execute(
        text(
            """
            INSERT INTO tour_assignment_logs
                (schedule_id, guide_id, assigned_by, assignment_type, action)
            VALUES
                (:schedule_id, :guide_id, 'system', 'AUTO', 'UNASSIGNED')
            """
        ),
        {"schedule_id": schedule_id, "guide_id": old_guide_id},
    )
    events.append({
        "type": "GUIDE_UNASSIGNED",
        "schedule_id": schedule_id,
        "guide_id": old_guide_id,
        "reason": "Guide requested cancellation",
    })

    try:
        result = auto_assign_guide(conn, schedule_id, commit=False)
        # Extract notification event from result
        if "_notification_event" in result:
            events.append(result["_notification_event"])
        conn.commit()
        return {
            "schedule_id": schedule_id,
            "old_guide_id": old_guide_id,
            "new_guide_id": result["guide_id"],
            "new_guide_name": result["guide_name"],
            "status": "ASSIGNED",
            "_notification_events": events,
        }
    except UnassignableError as exc:
        # Extract notification event from exception
        if hasattr(exc, "notification_event"):
            events.append(exc.notification_event)
        conn.commit()
        return {
            "schedule_id": schedule_id,
            "old_guide_id": old_guide_id,
            "new_guide_id": None,
            "status": "UNASSIGNABLE",
            "reasons": exc.reasons,
            "_notification_events": events,
        }
