from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from .db import test_connection, engine
from pydantic import BaseModel
from datetime import date

app = FastAPI(title="My Project API")

# Allow Vue dev server to talk to FastAPI
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://*.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request bodies
class BookingCreate(BaseModel):
    customer_id: str
    tour_id: int
    date: date
    adult_tickets: int
    child_tickets: int

class BookingReschedule(BaseModel):
    new_date: date

class IssueCreate(BaseModel):
    description: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    try:
        value = test_connection()
        return {"status": "ok", "db_check": value}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/group_members_example")
def read_group_members():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM group_members"))
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
        return rows
    except Exception as e:
        return {"status": "error", "detail": str(e)}


# ==================== GUIDES ====================
@app.get("/guides")
def read_guides():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM guides ORDER BY name"))
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
        return rows
    except Exception as e:
        return {"status": "error", "detail": str(e)}


# ==================== TOURS ====================
@app.get("/tours")
def read_tours():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM tours ORDER BY tour_name"))
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
        return rows
    except Exception as e:
        return {"status": "error", "detail": str(e)}


# ==================== NOTIFICATIONS ====================
@app.get("/notifications")
def read_notifications():
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT * FROM notifications ORDER BY created_at DESC LIMIT 10")
            )
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
        return rows
    except Exception as e:
        return {"status": "error", "detail": str(e)}


# ==================== BOOKINGS ====================
@app.get("/bookings")
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


@app.post("/bookings")
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
                }
            )
            connection.commit()
            columns = result.keys()
            row = result.fetchone()
            return dict(zip(columns, row))
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.patch("/bookings/{booking_id}/reschedule")
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
                {"new_date": reschedule.new_date, "booking_id": booking_id}
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


@app.patch("/bookings/{booking_id}/cancel")
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
                {"booking_id": booking_id}
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


# ==================== ISSUES ====================
@app.post("/issues")
def create_issue(issue: IssueCreate):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    INSERT INTO issues (description)
                    VALUES (:description)
                    RETURNING *
                """),
                {"description": issue.description}
            )
            connection.commit()
            columns = result.keys()
            row = result.fetchone()
            return dict(zip(columns, row))
    except Exception as e:
        return {"status": "error", "detail": str(e)}


# ==================== STATS ====================
@app.get("/stats")
def read_stats():
    try:
        with engine.connect() as connection:
            # Get today's date
            from datetime import date
            today = date.today()
            
            # Tours today
            tours_result = connection.execute(
                text("""
                    SELECT COUNT(*) as count 
                    FROM bookings 
                    WHERE date = :today AND status != 'cancelled'
                """),
                {"today": today}
            )
            tours_today = tours_result.scalar() or 0
            
            # Customers today
            customers_result = connection.execute(
                text("""
                    SELECT COALESCE(SUM(adult_tickets + child_tickets), 0) as total
                    FROM bookings 
                    WHERE date = :today AND status != 'cancelled'
                """),
                {"today": today}
            )
            customers_today = customers_result.scalar() or 0
            
            # Cancellations today
            cancellations_result = connection.execute(
                text("""
                    SELECT COUNT(*) as count
                    FROM bookings 
                    WHERE date = :today AND status = 'cancelled'
                """),
                {"today": today}
            )
            cancellations = cancellations_result.scalar() or 0
            
            # Average guide rating (if you add this column)
            avg_rating = 5.0
            
            return {
                "toursToday": int(tours_today),
                "customersToday": int(customers_today),
                "cancellations": int(cancellations),
                "avgRating": str(avg_rating)
            }
    except Exception as e:
        return {"status": "error", "detail": str(e)}