from __future__ import annotations

import logging

from sqlalchemy import text

from .exceptions import NotFoundError, UnassignableError
from .guide_assignment import auto_assign_guide
from .notification import create_notification

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
) -> int:
    """Find a matching schedule or create a new one and attempt guide assignment."""
    schedule_id = find_matching_schedule(conn, tour_id, language_code, event_start_datetime)
    if schedule_id is not None:
        return schedule_id

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
        create_notification(
            conn,
            event_type="GUIDE_ASSIGNED",
            schedule_id=schedule_id,
            guide_id=result["guide_id"],
            message=f"Guide {result['guide_name']} auto-assigned to new schedule {schedule_id}",
        )
    except UnassignableError as exc:
        create_notification(
            conn,
            event_type="SCHEDULE_UNASSIGNABLE",
            schedule_id=schedule_id,
            guide_id=None,
            message=f"No eligible guide for schedule {schedule_id}: {', '.join(exc.reasons)}",
        )

    return schedule_id


def cleanup_empty_schedule(conn, schedule_id: int) -> None:
    """Cancel a schedule and unassign its guide if no active reservations remain."""
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
        return

    schedule = conn.execute(
        text("SELECT id, guide_id FROM schedule WHERE id = :id"),
        {"id": schedule_id},
    ).fetchone()
    if not schedule:
        return

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
        create_notification(
            conn,
            event_type="GUIDE_REASSIGNED",
            schedule_id=schedule_id,
            guide_id=old_guide_id,
            message=f"Guide unassigned from cancelled schedule {schedule_id}",
        )


def handle_reservation_change(
    conn,
    reservation_id: int,
    old_schedule_id: int | None,
    new_tour_id: int,
    new_language_code: str,
    new_event_start,
    new_event_end,
) -> None:
    """FR-1/FR-2/FR-3: Move a reservation whose tour, language, or time changed."""
    conn.execute(
        text("UPDATE reservations SET schedule_id = NULL WHERE id = :id"),
        {"id": reservation_id},
    )

    new_schedule_id = find_or_create_schedule(conn, new_tour_id, new_language_code, new_event_start, new_event_end)

    conn.execute(
        text("UPDATE reservations SET schedule_id = :sid WHERE id = :id"),
        {"sid": new_schedule_id, "id": reservation_id},
    )

    create_notification(
        conn,
        event_type="RESERVATION_MOVED",
        schedule_id=new_schedule_id,
        guide_id=None,
        message=(
            f"Reservation {reservation_id} moved to schedule {new_schedule_id}"
            + (f" from schedule {old_schedule_id}" if old_schedule_id else "")
        ),
    )

    if old_schedule_id is not None:
        cleanup_empty_schedule(conn, old_schedule_id)


def handle_reservation_cancellation(
    conn,
    reservation_id: int,
    old_schedule_id: int,
) -> None:
    """FR-4: Clean up after a reservation is cancelled."""
    create_notification(
        conn,
        event_type="RESERVATION_CANCELLED",
        schedule_id=old_schedule_id,
        guide_id=None,
        message=f"Reservation {reservation_id} cancelled and removed from schedule {old_schedule_id}",
    )
    cleanup_empty_schedule(conn, old_schedule_id)


def handle_guide_cancellation(conn, schedule_id: int) -> dict:
    """FR-5: Unassign a guide and attempt to find a replacement."""
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
        return {"schedule_id": schedule_id, "status": sched["status"], "message": "No guide was assigned"}

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
    create_notification(
        conn,
        event_type="GUIDE_REASSIGNED",
        schedule_id=schedule_id,
        guide_id=old_guide_id,
        message=f"Guide {old_guide_id} removed from schedule {schedule_id}",
    )

    try:
        result = auto_assign_guide(conn, schedule_id, commit=False)
        create_notification(
            conn,
            event_type="GUIDE_ASSIGNED",
            schedule_id=schedule_id,
            guide_id=result["guide_id"],
            message=f"Replacement guide {result['guide_name']} assigned to schedule {schedule_id}",
        )
        conn.commit()
        return {
            "schedule_id": schedule_id,
            "old_guide_id": old_guide_id,
            "new_guide_id": result["guide_id"],
            "new_guide_name": result["guide_name"],
            "status": "ASSIGNED",
        }
    except UnassignableError as exc:
        create_notification(
            conn,
            event_type="SCHEDULE_UNASSIGNABLE",
            schedule_id=schedule_id,
            guide_id=None,
            message=f"No replacement guide for schedule {schedule_id}: {', '.join(exc.reasons)}",
        )
        conn.commit()
        return {
            "schedule_id": schedule_id,
            "old_guide_id": old_guide_id,
            "new_guide_id": None,
            "status": "UNASSIGNABLE",
            "reasons": exc.reasons,
        }
