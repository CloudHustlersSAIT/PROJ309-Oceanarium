from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import text

from .exceptions import ConflictError, NotFoundError, ValidationError


def list_reservations(conn):
    # Read path only: return newest reservations first for dashboard-style views.
    result = conn.execute(text("SELECT * FROM reservations ORDER BY created_at DESC"))
    columns = result.keys()
    rows = [dict(zip(columns, row)) for row in result.fetchall()]
    return rows


def create_reservation(conn, data):
    # Manual booking flow still sends ticket breakdown; persist as aggregate count.
    if data.adult_tickets < 0 or data.child_tickets < 0:
        raise ValidationError("Ticket count cannot be negative")

    if data.adult_tickets == 0 and data.child_tickets == 0:
        raise ValidationError("At least one ticket must be booked")

    # Validate FK parents early to return explicit domain errors.
    customer = conn.execute(
        text(
            """
            SELECT id
            FROM customers
            WHERE id = :customer_id
            """
        ),
        {"customer_id": data.customer_id},
    ).fetchone()

    if not customer:
        raise NotFoundError("Customer not found")

    # Create receives schedule_id; derive tour_id, language, and start datetime from schedule.
    schedule = conn.execute(
        text(
            """
            SELECT id, event_start_datetime, tour_id, language_code
            FROM schedule
            WHERE id = :schedule_id
            """
        ),
        {"schedule_id": data.schedule_id},
    ).fetchone()

    if not schedule:
        # reservations.tour_id is NOT NULL, so schedule must exist to infer a valid tour.
        raise NotFoundError("Schedule not found")

    schedule_id = schedule.id
    tour_id = schedule.tour_id
    language_code = schedule.language_code
    event_start = schedule.event_start_datetime
    if isinstance(event_start, datetime) and event_start.tzinfo is None:
        event_start = event_start.replace(tzinfo=timezone.utc)

    # Accept client-provided external ID, otherwise generate deterministic manual prefix.
    clorian_reservation_id = (
        (data.clorian_reservation_id or "").strip() if hasattr(data, "clorian_reservation_id") else ""
    )
    if not clorian_reservation_id:
        clorian_reservation_id = f"MANUAL-{uuid4().hex[:12].upper()}"

    existing = conn.execute(
        text(
            """
            SELECT 1
            FROM reservations
            WHERE clorian_reservation_id = :clorian_reservation_id
            """
        ),
        {"clorian_reservation_id": clorian_reservation_id},
    ).fetchone()
    if existing:
        raise ConflictError("Reservation with this clorian_reservation_id already exists")

    # Prevent duplicate reservations for the same customer in the same schedule.
    duplicate_customer_schedule = conn.execute(
        text(
            """
            SELECT 1
            FROM reservations
            WHERE customer_id = :customer_id
              AND schedule_id = :schedule_id
              AND status != 'CANCELLED'
            """
        ),
        {
            "customer_id": data.customer_id,
            "schedule_id": schedule_id,
        },
    ).fetchone()
    if duplicate_customer_schedule:
        raise ConflictError("Customer already has a reservation for this schedule")

    # Persist status in a normalized uppercase representation.
    status = (data.status or "CONFIRMED").strip().upper()

    clorian_purchase_id = data.clorian_purchase_id

    result = conn.execute(
        text("""
            INSERT INTO reservations
            (clorian_reservation_id, clorian_purchase_id, customer_id, tour_id, schedule_id,
             language_code, event_start_datetime, status, current_ticket_num,
             clorian_created_at, clorian_modified_at)
            VALUES
            (:clorian_reservation_id, :clorian_purchase_id, :customer_id, :tour_id, :schedule_id,
             :language_code, :event_start_datetime, :status, :current_ticket_num,
             NOW(), NOW())
            RETURNING *
        """),
        {
            "clorian_reservation_id": clorian_reservation_id,
            "clorian_purchase_id": clorian_purchase_id,
            "customer_id": data.customer_id,
            "tour_id": tour_id,
            "schedule_id": schedule_id,
            "language_code": language_code,
            "event_start_datetime": event_start,
            "status": status,
            "current_ticket_num": data.adult_tickets + data.child_tickets,
        },
    )

    conn.commit()

    columns = result.keys()
    row = result.fetchone()
    return dict(zip(columns, row))


def reschedule_reservation(conn, reservation_id, data):
    existing = conn.execute(
        text("""
            SELECT id, status, customer_id
            FROM reservations
            WHERE id = :reservation_id
        """),
        {"reservation_id": reservation_id},
    ).fetchone()

    if not existing:
        raise NotFoundError("Reservation not found")

    if str(existing.status).strip().upper() == "CANCELLED":
        raise ValidationError("Cannot reschedule cancelled reservation")

    new_schedule = conn.execute(
        text(
            """
            SELECT id, event_start_datetime, tour_id, language_code
            FROM schedule
            WHERE id = :schedule_id
            """
        ),
        {"schedule_id": data.new_schedule_id},
    ).fetchone()

    if not new_schedule:
        raise NotFoundError("Schedule not found")

    # Keep the same single-booking-per-customer-per-schedule rule on reschedule.
    duplicate_customer_schedule = conn.execute(
        text(
            """
            SELECT 1
            FROM reservations
            WHERE customer_id = :customer_id
              AND schedule_id = :schedule_id
              AND id <> :reservation_id
              AND status != 'CANCELLED'
            """
        ),
        {
            "customer_id": existing.customer_id,
            "schedule_id": new_schedule.id,
            "reservation_id": reservation_id,
        },
    ).fetchone()
    if duplicate_customer_schedule:
        raise ConflictError("Customer already has a reservation for this schedule")

    new_event_start = new_schedule.event_start_datetime
    if isinstance(new_event_start, datetime) and new_event_start.tzinfo is None:
        new_event_start = new_event_start.replace(tzinfo=timezone.utc)

    result = conn.execute(
        text("""
            UPDATE reservations
            -- Align reservation with the selected schedule values.
            SET event_start_datetime = :event_start_datetime,
                schedule_id = :schedule_id,
                tour_id = :tour_id,
                language_code = :language_code,
                clorian_modified_at = NOW()
            WHERE id = :reservation_id
            RETURNING *
        """),
        {
            "event_start_datetime": new_event_start,
            "schedule_id": new_schedule.id,
            "tour_id": new_schedule.tour_id,
            "language_code": new_schedule.language_code,
            "reservation_id": reservation_id,
        },
    )

    conn.commit()

    columns = result.keys()
    row = result.fetchone()
    return dict(zip(columns, row))


def cancel_reservation(conn, booking_id):
    existing = conn.execute(
        text("""
            SELECT status
            FROM reservations
            WHERE id = :reservation_id
        """),
        {"reservation_id": booking_id},
    ).fetchone()

    if not existing:
        raise NotFoundError("Reservation not found")

    if str(existing.status).strip().upper() == "CANCELLED":
        raise ValidationError("Reservation is already cancelled")

    result = conn.execute(
        text("""
            UPDATE reservations
            -- Keep historical row and mark cancellation instead of deleting.
            SET status = 'CANCELLED',
                schedule_id = NULL,
                clorian_modified_at = NOW()
            WHERE id = :reservation_id
            RETURNING *
        """),
        {"reservation_id": booking_id},
    )
    columns = result.keys()
    row = result.fetchone()

    conn.commit()

    return dict(zip(columns, row))
