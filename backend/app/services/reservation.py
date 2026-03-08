from datetime import datetime

from sqlalchemy import text

from .exceptions import ConflictError, NotFoundError, ValidationError


def _has_language_column(conn):
    result = conn.execute(
        text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'reservations'
            AND column_name = 'language'
            LIMIT 1
            """
        )
    ).fetchone()
    return bool(result)


def list_reservations(conn):
    result = conn.execute(
        text("SELECT * FROM reservations ORDER BY created_at DESC")
    )
    columns = result.keys()
    rows = [dict(zip(columns, row)) for row in result.fetchall()]
    return rows


def create_reservation(conn, data):
    if data.adult_tickets < 0 or data.child_tickets < 0:
        raise ValidationError("Ticket count cannot be negative")

    if data.adult_tickets == 0 and data.child_tickets == 0:
        raise ValidationError("At least one ticket must be booked")

    tour = conn.execute(
        text("""
            SELECT id
            FROM tours
            WHERE id = :tour_id
        """),
        {"tour_id": data.tour_id},
    ).fetchone()

    if not tour:
        raise NotFoundError("Tour not found")

    # Basic duplicate guard with current schema: same tour, same datetime, active status.
    event_start = datetime.combine(data.date, data.start_time)
    conflict = conn.execute(
        text("""
            SELECT 1
            FROM reservations
            WHERE tour_id = :tour_id
            AND event_start_datetime = :event_start_datetime
            AND (status IS NULL OR status != 'cancelled')
        """),
        {
            "tour_id": data.tour_id,
            "event_start_datetime": event_start,
        },
    ).fetchone()

    if conflict:
        raise ConflictError(
            "A reservation already exists for this tour and start time")

    next_clorian_reservation_id = conn.execute(
        text(
            """
            SELECT COALESCE(MAX(clorian_reservation_id), 0) + 1
            FROM reservations
            """
        )
    ).scalar_one()

    supports_language = _has_language_column(conn)
    payload = {
        "clorian_reservation_id": next_clorian_reservation_id,
        "customer_id": data.customer_id,
        "tour_id": data.tour_id,
        "event_start_datetime": event_start,
        "current_ticket_num": data.adult_tickets + data.child_tickets,
        "language": getattr(data, "language", None) or "English",
    }

    if supports_language:
        result = conn.execute(
            text("""
                INSERT INTO reservations
                (clorian_reservation_id, customer_id, tour_id,
                 event_start_datetime, status, current_ticket_num, language)
                VALUES
                (:clorian_reservation_id, :customer_id, :tour_id,
                 :event_start_datetime, 'confirmed', :current_ticket_num, :language)
                RETURNING *
            """),
            payload,
        )
    else:
        result = conn.execute(
            text("""
                INSERT INTO reservations
                (clorian_reservation_id, customer_id, tour_id,
                 event_start_datetime, status, current_ticket_num)
                VALUES
                (:clorian_reservation_id, :customer_id, :tour_id,
                 :event_start_datetime, 'confirmed', :current_ticket_num)
                RETURNING *
            """),
            payload,
        )

    conn.commit()

    columns = result.keys()
    row = result.fetchone()
    return dict(zip(columns, row))


def reschedule_reservation(conn, reservation_id, data):
    new_event_start = datetime.combine(data.new_date, data.start_time)

    existing = conn.execute(
        text("""
            SELECT id, status
            FROM reservations
            WHERE id = :reservation_id
        """),
        {"reservation_id": reservation_id},
    ).fetchone()

    if not existing:
        raise NotFoundError("Reservation not found")

    if existing.status == "cancelled":
        raise ValidationError("Cannot reschedule cancelled reservation")

    result = conn.execute(
        text("""
            UPDATE reservations
            SET event_start_datetime = :event_start_datetime
            WHERE id = :reservation_id
            RETURNING *
        """),
        {
            "event_start_datetime": new_event_start,
            "reservation_id": reservation_id,
        },
    )

    conn.commit()

    columns = result.keys()
    row = result.fetchone()
    return dict(zip(columns, row))


def cancel_reservation(conn, reservation_id):
    existing = conn.execute(
        text("""
            SELECT status
            FROM reservations
            WHERE id = :reservation_id
        """),
        {"reservation_id": reservation_id},
    ).fetchone()

    if not existing:
        raise NotFoundError("Reservation not found")

    if existing.status == "cancelled":
        raise ValidationError("Reservation is already cancelled")

    result = conn.execute(
        text("""
            UPDATE reservations
            SET status = 'cancelled'
            WHERE id = :reservation_id
            RETURNING *
        """),
        {"reservation_id": reservation_id},
    )
    columns = result.keys()
    row = result.fetchone()

    conn.commit()

    return dict(zip(columns, row))
