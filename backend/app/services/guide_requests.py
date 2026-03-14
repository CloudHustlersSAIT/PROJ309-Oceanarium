from sqlalchemy import text

from .exceptions import ValidationError


def get_swap_requests(conn, guide_id: int):
    sql = text(
        """
        SELECT
            tal.id AS swap_request_id,
            s.id AS schedule_id,
            t.name AS tour_name,
            s.event_start_datetime,
            s.event_end_datetime,
            requester.first_name AS requesting_guide_first_name,
            requester.last_name AS requesting_guide_last_name
        FROM tour_assignment_logs tal
        JOIN schedule s ON s.id = tal.schedule_id
        JOIN tours t ON t.id = s.tour_id
        JOIN guides requester ON requester.id = s.guide_id
        WHERE tal.action = 'SWAP_REQUEST'
          AND tal.assignment_type = 'SWAP'
          AND tal.guide_id = :guide_id
          AND NOT EXISTS (
              SELECT 1
              FROM tour_assignment_logs resolved
              WHERE resolved.schedule_id = tal.schedule_id
                AND resolved.guide_id = tal.guide_id
                AND resolved.assignment_type = 'SWAP'
                AND resolved.action IN ('SWAP_ACCEPTED', 'SWAP_REJECTED')
                AND resolved.assigned_at >= tal.assigned_at
          )
        """
    )

    result = conn.execute(sql, {"guide_id": guide_id})
    return result.mappings().all()


def create_swap_request(conn, schedule_id: int, guide_id: int, requesting_guide_id: int | None = None):
    schedule_sql = text(
        """
        SELECT id, guide_id
        FROM schedule
        WHERE id = :schedule_id
        """
    )
    schedule_row = conn.execute(schedule_sql, {"schedule_id": schedule_id}).mappings().first()
    if schedule_row is None:
        raise ValueError("Schedule not found")

    if requesting_guide_id is not None and schedule_row["guide_id"] != requesting_guide_id:
        raise ValueError("Swap request can only be created by the assigned guide")

    sql = text(
        """
        INSERT INTO tour_assignment_logs
            (schedule_id, guide_id, assigned_at, assigned_by, assignment_type, action)
        VALUES
            (:schedule_id, :guide_id, NOW(), 'guide', 'SWAP', 'SWAP_REQUEST')
        RETURNING id
        """
    )

    result = conn.execute(
        sql,
        {
            "schedule_id": schedule_id,
            "guide_id": guide_id,
        },
    )

    row = result.fetchone()
    conn.commit()

    return {"swap_request_id": row[0]} if row is not None else None


def get_swap_candidates(conn, schedule_id: int):
    sql = text(
        """
        WITH target AS (
            SELECT
                id,
                guide_id,
                event_start_datetime,
                event_end_datetime
            FROM schedule
            WHERE id = :schedule_id
        )
        SELECT
            g.id AS guide_id,
            g.first_name,
            g.last_name,
            g.guide_rating
        FROM guides g
        CROSS JOIN target t
        WHERE g.is_active = TRUE
          AND (t.guide_id IS NULL OR g.id <> t.guide_id)
          AND NOT EXISTS (
              SELECT 1
              FROM schedule s2
              WHERE s2.guide_id = g.id
                AND s2.status IN ('ASSIGNED', 'CONFIRMED')
                AND s2.event_start_datetime < t.event_end_datetime
                AND s2.event_end_datetime   > t.event_start_datetime
          )
        ORDER BY g.guide_rating DESC NULLS LAST
        """
    )

    result = conn.execute(sql, {"schedule_id": schedule_id})
    return result.mappings().all()


def accept_swap_request(conn, swap_request_id: int, caller_guide_id: int):
    """Accept a swap request. Only the candidate guide (stored in the log) may accept."""
    fetch_sql = text(
        """
        SELECT
            schedule_id,
            guide_id
        FROM tour_assignment_logs
        WHERE id = :swap_request_id
          AND action = 'SWAP_REQUEST'
          AND assignment_type = 'SWAP'
        """
    )

    row = conn.execute(fetch_sql, {"swap_request_id": swap_request_id}).mappings().first()
    if row is None:
        return {"status": "not_found"}

    if row["guide_id"] != caller_guide_id:
        raise ValidationError("Only the selected guide can accept this swap request")

    schedule_id = row["schedule_id"]
    guide_id = row["guide_id"]

    update_sql = text(
        """
        UPDATE schedule
        SET guide_id = :guide_id
        WHERE id = :schedule_id
        """
    )
    conn.execute(update_sql, {"guide_id": guide_id, "schedule_id": schedule_id})

    insert_sql = text(
        """
        INSERT INTO tour_assignment_logs
            (schedule_id, guide_id, assigned_at, assigned_by, assignment_type, action)
        VALUES
            (:schedule_id, :guide_id, NOW(), 'guide', 'SWAP', 'SWAP_ACCEPTED')
        """
    )
    conn.execute(insert_sql, {"schedule_id": schedule_id, "guide_id": guide_id})

    conn.commit()

    return {
        "status": "accepted",
        "schedule_id": schedule_id,
        "guide_id": guide_id,
    }


def reject_swap_request(conn, swap_request_id: int, caller_guide_id: int):
    """Reject a swap request. Only the candidate guide (stored in the log) may reject."""
    fetch_sql = text(
        """
        SELECT
            schedule_id,
            guide_id
        FROM tour_assignment_logs
        WHERE id = :swap_request_id
          AND action = 'SWAP_REQUEST'
          AND assignment_type = 'SWAP'
        """
    )

    row = conn.execute(fetch_sql, {"swap_request_id": swap_request_id}).mappings().first()
    if row is None:
        return {"status": "not_found"}

    if row["guide_id"] != caller_guide_id:
        raise ValidationError("Only the selected guide can reject this swap request")

    schedule_id = row["schedule_id"]
    guide_id = row["guide_id"]

    insert_sql = text(
        """
        INSERT INTO tour_assignment_logs
            (schedule_id, guide_id, assigned_at, assigned_by, assignment_type, action)
        VALUES
            (:schedule_id, :guide_id, NOW(), 'guide', 'SWAP', 'SWAP_REJECTED')
        """
    )
    conn.execute(insert_sql, {"schedule_id": schedule_id, "guide_id": guide_id})

    conn.commit()

    return {
        "status": "rejected",
        "schedule_id": schedule_id,
        "guide_id": guide_id,
    }

