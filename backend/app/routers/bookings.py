from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from ..db import engine
from ..schemas.booking import BookingCreate, BookingReschedule

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("")
def read_bookings():
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT * FROM bookings ORDER BY created_at DESC")
            )
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
        return rows
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.post("")
def create_booking(booking: BookingCreate):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    INSERT INTO bookings (customer_id, tour_id, date, adult_tickets, child_tickets, status)
                    VALUES (:customer_id, :tour_id, :date, :adult_tickets, :child_tickets, 'confirmed')
                    RETURNING *
                """),
                {
                    "customer_id": booking.customer_id,
                    "tour_id": booking.tour_id,
                    "date": booking.date,
                    "adult_tickets": booking.adult_tickets,
                    "child_tickets": booking.child_tickets,
                },
            )
            connection.commit()
            columns = result.keys()
            row = result.fetchone()
            return dict(zip(columns, row))
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.patch("/{booking_id}/reschedule")
def reschedule_booking(booking_id: int, reschedule: BookingReschedule):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    UPDATE bookings
                    SET date = :new_date
                    WHERE booking_id = :booking_id
                    RETURNING *
                """),
                {"new_date": reschedule.new_date, "booking_id": booking_id},
            )
            connection.commit()

            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Booking not found")

            columns = result.keys()
            row = result.fetchone()
            return dict(zip(columns, row))
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.patch("/{booking_id}/cancel")
def cancel_booking(booking_id: int):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    UPDATE bookings
                    SET status = 'cancelled'
                    WHERE booking_id = :booking_id
                    RETURNING *
                """),
                {"booking_id": booking_id},
            )
            connection.commit()

            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Booking not found")

            columns = result.keys()
            row = result.fetchone()
            return dict(zip(columns, row))
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "detail": str(e)}
