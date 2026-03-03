"""Reservation service -- booking CRUD with conflict detection.

Handles listing, creating, rescheduling, and cancelling bookings.
Each function validates business rules and raises domain exceptions
on failure so the route layer can map them to HTTP status codes.

Note: File is named ``reservation.py`` to align with ADR-001 domain naming,
but the underlying table and API paths still use ``bookings`` for backward
compatibility.
"""

from sqlalchemy import text

from .exceptions import ConflictError, NotFoundError, ValidationError


def list_reservations(conn):
    """Return all bookings ordered by creation date (newest first).

    Args:
        conn: SQLAlchemy connection provided by the route via ``Depends(get_db)``.

    Returns:
        list[dict]: Each dict maps column name to value for one booking row.
    """
    result = conn.execute(
        text("SELECT * FROM bookings ORDER BY created_at DESC")
    )
    columns = result.keys()
    rows = [dict(zip(columns, row)) for row in result.fetchall()]
    return rows


def create_reservation(conn, data):
    """Create a new booking after validating tickets and checking for conflicts.

    Validation steps:
        1. Ticket counts must be non-negative.
        2. At least one ticket (adult or child) must be booked.
        3. The referenced tour must exist.
        4. The guide assigned to that tour must not have an overlapping active
           booking on the same date/time.

    Args:
        conn: SQLAlchemy connection.
        data: Pydantic ``BookingCreate`` model with fields ``customer_id``,
              ``tour_id``, ``date``, ``start_time``, ``end_time``,
              ``adult_tickets``, ``child_tickets``.

    Returns:
        dict: The newly created booking row.

    Raises:
        ValidationError: Ticket counts are invalid.
        NotFoundError: Tour does not exist.
        ConflictError: Guide already has an overlapping booking.
    """
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

    # Overlap check: any active booking for the same guide whose time window
    # intersects the requested window. Uses the standard interval overlap test:
    # existing.start < new.end AND existing.end > new.start
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
    """Move an existing booking to a new date/time after conflict checks.

    Validation steps:
        1. Booking must exist.
        2. Booking must not already be cancelled.
        3. The guide must not have an overlapping active booking at the new time
           (excluding the current booking itself).

    Args:
        conn: SQLAlchemy connection.
        booking_id (int): Primary key of the booking to reschedule.
        data: Pydantic ``BookingReschedule`` model with ``new_date``,
              ``start_time``, ``end_time``.

    Returns:
        dict: The updated booking row.

    Raises:
        NotFoundError: Booking does not exist.
        ValidationError: Booking is cancelled.
        ConflictError: Guide already has an overlapping booking at the new time.
    """
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
    """Mark a booking as cancelled. Idempotent guard prevents double-cancel.

    Args:
        conn: SQLAlchemy connection.
        booking_id (int): Primary key of the booking to cancel.

    Returns:
        dict: The updated booking row with ``status='cancelled'``.

    Raises:
        NotFoundError: Booking does not exist.
        ValidationError: Booking is already cancelled.
    """
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
