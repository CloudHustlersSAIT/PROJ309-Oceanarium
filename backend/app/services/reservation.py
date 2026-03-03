from sqlalchemy import text

from .exceptions import ConflictError, NotFoundError, ValidationError


def list_reservations(conn):
    result = conn.execute(
        text("SELECT * FROM bookings ORDER BY created_at DESC")
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
            SELECT guide_id
            FROM tours
            WHERE tour_id = :tour_id
        """),
        {"tour_id": data.tour_id},
    ).fetchone()

    if not tour:
        raise NotFoundError("Tour not found")

    conflict = conn.execute(
        text("""
            SELECT 1
            FROM bookings b
            JOIN tours t ON b.tour_id = t.tour_id
            WHERE t.guide_id = :guide_id
            AND b.date = :date
            AND :start_time < b.end_time
            AND :end_time > b.start_time
            AND (b.status IS NULL OR b.status != 'cancelled')
        """),
        {
            "guide_id": tour.guide_id,
            "date": data.date,
            "start_time": data.start_time,
            "end_time": data.end_time,
        },
    ).fetchone()

    if conflict:
        raise ConflictError("Guide already has overlapping booking")

    result = conn.execute(
        text("""
            INSERT INTO bookings
            (customer_id, tour_id, date, start_time, end_time,
             adult_tickets, child_tickets, status)
            VALUES
            (:customer_id, :tour_id, :date, :start_time, :end_time,
             :adult_tickets, :child_tickets, 'confirmed')
            RETURNING *
        """),
        {
            "customer_id": data.customer_id,
            "tour_id": data.tour_id,
            "date": data.date,
            "start_time": data.start_time,
            "end_time": data.end_time,
            "adult_tickets": data.adult_tickets,
            "child_tickets": data.child_tickets,
        },
    )

    conn.commit()

    columns = result.keys()
    row = result.fetchone()
    return dict(zip(columns, row))


def reschedule_reservation(conn, booking_id, data):
    existing = conn.execute(
        text("""
            SELECT booking_id, tour_id, date, status
            FROM bookings
            WHERE booking_id = :booking_id
        """),
        {"booking_id": booking_id},
    ).fetchone()

    if not existing:
        raise NotFoundError("Booking not found")

    if existing.status == "cancelled":
        raise ValidationError("Cannot reschedule cancelled booking")

    conflict = conn.execute(
        text("""
            SELECT 1
            FROM bookings b
            JOIN tours t ON b.tour_id = t.tour_id
            WHERE t.guide_id = (
                SELECT guide_id FROM tours WHERE tour_id = :tour_id
            )
            AND b.date = :new_date
            AND :start_time < b.end_time
            AND :end_time > b.start_time
            AND b.booking_id != :booking_id
            AND (b.status IS NULL OR b.status != 'cancelled')
        """),
        {
            "tour_id": existing.tour_id,
            "new_date": data.new_date,
            "start_time": data.start_time,
            "end_time": data.end_time,
            "booking_id": booking_id,
        },
    ).fetchone()

    if conflict:
        raise ConflictError("Guide already has overlapping booking")

    result = conn.execute(
        text("""
            UPDATE bookings
            SET date = :new_date,
                start_time = :start_time,
                end_time = :end_time
            WHERE booking_id = :booking_id
            RETURNING *
        """),
        {
            "new_date": data.new_date,
            "start_time": data.start_time,
            "end_time": data.end_time,
            "booking_id": booking_id,
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
            FROM bookings 
            WHERE booking_id = :booking_id
        """),
        {"booking_id": booking_id},
    ).fetchone()

    if not existing:
        raise NotFoundError("Booking not found")

    if existing.status == "cancelled":
        raise ValidationError("Booking is already cancelled")

    result = conn.execute(
        text("""
            UPDATE bookings 
            SET status = 'cancelled' 
            WHERE booking_id = :booking_id 
            RETURNING *
        """),
        {"booking_id": booking_id},
    )
    columns = result.keys()
    row = result.fetchone()

    conn.commit()

    return dict(zip(columns, row))
