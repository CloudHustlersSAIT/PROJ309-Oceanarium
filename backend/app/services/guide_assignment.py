from __future__ import annotations

from sqlalchemy import text

from .exceptions import NotFoundError, UnassignableError, ValidationError


def _fetch_schedule(conn, schedule_id: int) -> dict:
    row = conn.execute(
        text(
            """
            SELECT id, guide_id, tour_id, language_code,
                   event_start_datetime, event_end_datetime, status
            FROM schedule
            WHERE id = :schedule_id
            """
        ),
        {"schedule_id": schedule_id},
    ).fetchone()
    if not row:
        raise NotFoundError("Schedule not found")
    return dict(row._mapping)


def _guides_matching_language(conn, language_code: str) -> list[int]:
    """FR-1: Active guides who speak the required language."""
    rows = conn.execute(
        text(
            """
            SELECT DISTINCT g.id
            FROM guides g
            JOIN guide_languages gl ON gl.guide_id = g.id
            JOIN languages l ON l.id = gl.language_id
                AND LOWER(l.code) = LOWER(:language_code)
            WHERE g.is_active = true
            """
        ),
        {"language_code": language_code},
    ).fetchall()
    return [r[0] for r in rows]


def _guides_matching_expertise(conn, guide_ids: list[int], tour_id: int) -> list[int]:
    """FR-3: Guides qualified for the specific tour type."""
    if not guide_ids:
        return []
    rows = conn.execute(
        text(
            """
            SELECT DISTINCT g.id
            FROM guides g
            JOIN guide_tour_types gtt ON gtt.guide_id = g.id
                AND gtt.tour_id = :tour_id
            WHERE g.id = ANY(:guide_ids)
              AND g.is_active = true
            """
        ),
        {"tour_id": tour_id, "guide_ids": guide_ids},
    ).fetchall()
    return [r[0] for r in rows]


def _guides_matching_availability(
    conn,
    guide_ids: list[int],
    event_start,
    event_end,
    exclude_schedule_id: int,
) -> list[int]:
    """FR-2: Guides available during the schedule's time window.

    Checks weekly availability slots (converted to guide's local timezone),
    excludes guides with BLOCKED exceptions, and excludes guides with
    overlapping schedules.
    """
    if not guide_ids:
        return []
    rows = conn.execute(
        text(
            """
            SELECT DISTINCT g.id
            FROM guides g
            JOIN availability_patterns ap ON ap.guide_id = g.id
            JOIN availability_slots asl ON asl.pattern_id = ap.id
            WHERE g.id = ANY(:guide_ids)
              AND LOWER(asl.day_of_week) = LOWER(
                  TRIM(TO_CHAR(
                      CAST(:event_start AS timestamptz) AT TIME ZONE ap.timezone,
                      'Day'
                  ))
              )
              AND asl.start_time <= (CAST(:event_start AS timestamptz) AT TIME ZONE ap.timezone)::time
              AND asl.end_time   >= (CAST(:event_end   AS timestamptz) AT TIME ZONE ap.timezone)::time
              AND NOT EXISTS (
                  SELECT 1
                  FROM availability_exceptions ae
                  WHERE ae.pattern_id = ap.id
                    AND ae.date = (CAST(:event_start AS timestamptz) AT TIME ZONE ap.timezone)::date
                    AND UPPER(ae.type) = 'BLOCKED'
              )
              AND NOT EXISTS (
                  SELECT 1
                  FROM schedule sx
                  WHERE sx.guide_id = g.id
                    AND sx.id != :exclude_schedule_id
                    AND sx.status IN ('ASSIGNED', 'CONFIRMED')
                    AND sx.event_start_datetime < :event_end
                    AND sx.event_end_datetime   > :event_start
              )
            """
        ),
        {
            "guide_ids": guide_ids,
            "event_start": event_start,
            "event_end": event_end,
            "exclude_schedule_id": exclude_schedule_id,
        },
    ).fetchall()
    return [r[0] for r in rows]


def _rank_guides(conn, guide_ids: list[int], schedule_date) -> list[dict]:
    """FR-4: Rank eligible guides by fewest same-day assignments, then
    highest rating, then lowest ID."""
    if not guide_ids:
        return []
    rows = conn.execute(
        text(
            """
            SELECT
                g.id,
                g.first_name,
                g.last_name,
                g.guide_rating,
                COUNT(s.id) AS same_day_assignments
            FROM guides g
            LEFT JOIN schedule s
                ON s.guide_id = g.id
               AND s.event_start_datetime::date = :schedule_date
               AND s.status IN ('ASSIGNED', 'CONFIRMED')
            WHERE g.id = ANY(:guide_ids)
            GROUP BY g.id, g.first_name, g.last_name, g.guide_rating
            ORDER BY
                same_day_assignments ASC,
                g.guide_rating DESC NULLS LAST,
                g.id ASC
            """
        ),
        {"guide_ids": guide_ids, "schedule_date": schedule_date},
    ).fetchall()

    return [
        {
            "id": r[0],
            "first_name": r[1],
            "last_name": r[2],
            "guide_rating": r[3],
            "same_day_assignments": r[4],
        }
        for r in rows
    ]


def find_eligible_guides(conn, schedule_id: int):
    """Find guides satisfying all three hard constraints for a schedule.

    Returns (ranked_guides, reasons) where reasons is empty when guides
    are found, or contains specific codes when no guide is eligible.
    """
    schedule = _fetch_schedule(conn, schedule_id)
    reasons: list[str] = []

    lang_ids = _guides_matching_language(conn, schedule["language_code"])
    if not lang_ids:
        reasons.append("NO_LANGUAGE_MATCH")
        return [], reasons

    expertise_ids = _guides_matching_expertise(conn, lang_ids, schedule["tour_id"])
    if not expertise_ids:
        reasons.append("NO_EXPERTISE_MATCH")
        return [], reasons

    avail_ids = _guides_matching_availability(
        conn,
        expertise_ids,
        schedule["event_start_datetime"],
        schedule["event_end_datetime"],
        schedule["id"],
    )
    if not avail_ids:
        reasons.append("NO_AVAILABILITY_MATCH")
        return [], reasons

    schedule_date = schedule["event_start_datetime"].date()
    ranked = _rank_guides(conn, avail_ids, schedule_date)
    return ranked, reasons


def auto_assign_guide(conn, schedule_id: int, *, commit: bool = True) -> dict:
    """Auto-assign the best eligible guide to a schedule (FDR-002 FR-1..FR-4)."""
    schedule = _fetch_schedule(conn, schedule_id)
    ranked, reasons = find_eligible_guides(conn, schedule_id)

    if not ranked:
        conn.execute(
            text("UPDATE schedule SET status = 'UNASSIGNABLE' WHERE id = :id"),
            {"id": schedule_id},
        )
        if commit:
            conn.commit()
        raise UnassignableError(
            "No eligible guide found for this schedule",
            reasons=reasons,
        )

    best = ranked[0]
    action = "REASSIGNED" if schedule["guide_id"] is not None else "ASSIGNED"

    conn.execute(
        text(
            """
            UPDATE schedule
            SET guide_id = :guide_id, status = 'ASSIGNED'
            WHERE id = :schedule_id
            """
        ),
        {"guide_id": best["id"], "schedule_id": schedule_id},
    )

    conn.execute(
        text(
            """
            INSERT INTO tour_assignment_logs
                (schedule_id, guide_id, assigned_by, assignment_type, action)
            VALUES
                (:schedule_id, :guide_id, :assigned_by, :assignment_type, :action)
            """
        ),
        {
            "schedule_id": schedule_id,
            "guide_id": best["id"],
            "assigned_by": "system",
            "assignment_type": "AUTO",
            "action": action,
        },
    )

    if commit:
        conn.commit()

    return {
        "schedule_id": schedule_id,
        "guide_id": best["id"],
        "guide_name": f"{best['first_name']} {best['last_name']}",
        "assignment_type": "AUTO",
        "constraints_met": {
            "language": True,
            "availability": True,
            "expertise": True,
        },
    }


def _check_constraint_warnings(conn, schedule: dict, guide_id: int) -> list[str]:
    """Check all three hard constraints for a specific guide, returning
    warning strings for any violations."""
    warnings: list[str] = []

    lang_match = conn.execute(
        text(
            """
            SELECT 1
            FROM guide_languages gl
            JOIN languages l ON l.id = gl.language_id
                AND LOWER(l.code) = LOWER(:language_code)
            WHERE gl.guide_id = :guide_id
            """
        ),
        {"guide_id": guide_id, "language_code": schedule["language_code"]},
    ).fetchone()
    if not lang_match:
        warnings.append(f"Guide does not speak requested language: {schedule['language_code']}")

    expertise_match = conn.execute(
        text(
            """
            SELECT 1
            FROM guide_tour_types gtt
            WHERE gtt.guide_id = :guide_id AND gtt.tour_id = :tour_id
            """
        ),
        {"guide_id": guide_id, "tour_id": schedule["tour_id"]},
    ).fetchone()
    if not expertise_match:
        warnings.append("Guide is not qualified for this tour type")

    avail_ids = _guides_matching_availability(
        conn,
        [guide_id],
        schedule["event_start_datetime"],
        schedule["event_end_datetime"],
        schedule["id"],
    )
    if guide_id not in avail_ids:
        warnings.append("Guide is not available during the schedule time window")

    return warnings


def manual_assign_guide(
    conn,
    schedule_id: int,
    guide_id: int,
    assigned_by: str,
    *,
    commit: bool = True,
) -> dict:
    """Manually assign a guide to a schedule (FDR-002 FR-5).

    Constraint violations produce warnings but do not block the assignment.
    """
    schedule = _fetch_schedule(conn, schedule_id)

    guide = conn.execute(
        text("SELECT id, first_name, last_name, is_active FROM guides WHERE id = :id"),
        {"id": guide_id},
    ).fetchone()
    if not guide:
        raise NotFoundError("Guide not found")
    if not guide.is_active:
        raise ValidationError("Guide is inactive")

    warnings = _check_constraint_warnings(conn, schedule, guide_id)

    action = "REASSIGNED" if schedule["guide_id"] is not None else "ASSIGNED"

    conn.execute(
        text(
            """
            UPDATE schedule
            SET guide_id = :guide_id, status = 'ASSIGNED'
            WHERE id = :schedule_id
            """
        ),
        {"guide_id": guide_id, "schedule_id": schedule_id},
    )

    conn.execute(
        text(
            """
            INSERT INTO tour_assignment_logs
                (schedule_id, guide_id, assigned_by, assignment_type, action)
            VALUES
                (:schedule_id, :guide_id, :assigned_by, :assignment_type, :action)
            """
        ),
        {
            "schedule_id": schedule_id,
            "guide_id": guide_id,
            "assigned_by": assigned_by,
            "assignment_type": "MANUAL",
            "action": action,
        },
    )

    if commit:
        conn.commit()

    return {
        "schedule_id": schedule_id,
        "guide_id": guide_id,
        "guide_name": f"{guide.first_name} {guide.last_name}",
        "assignment_type": "MANUAL",
        "warnings": warnings,
    }
