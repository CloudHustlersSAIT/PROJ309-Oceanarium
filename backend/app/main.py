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
    # Mock data for testing
    mock_guides = [
        {"id": 1, "name": "Ana Costa", "expertise": "Sharks", "rating": 4.9},
        {"id": 2, "name": "Hermes Costello", "expertise": "Dolphins", "rating": 4.8},
        {"id": 3, "name": "Chen Wei", "expertise": "Marine Biology", "rating": 4.7},
        {"id": 4, "name": "Liam Brown", "expertise": "Ocean History", "rating": 4.6},
    ]
    return mock_guides


# ==================== TOURS ====================
@app.get("/tours")
def read_tours():
    # Mock data for testing calendar integration
    mock_tours = [
        {
            "id": 1,
            "tour": "Shark Diving",
            "guide": "Ana Costa",
            "date": "2025-02-07",
            "time": "08:00",
            "participants": 5,
        },
        {
            "id": 2,
            "tour": "Dolphin Feeding",
            "guide": "Hermes Costello",
            "date": "2025-02-07",
            "time": "10:00",
            "participants": 8,
        },
        {
            "id": 3,
            "tour": "Deep Sea Experience",
            "guide": "Ann A. Kim",
            "date": "2025-02-08",
            "time": "14:00",
            "participants": 4,
        },
        {
            "id": 4,
            "tour": "Molluscs",
            "guide": "Chen Wei",
            "date": "2025-02-08",
            "time": "11:00",
            "participants": 6,
        },
        {
            "id": 5,
            "tour": "Coral Exploration",
            "guide": "Ana Costa",
            "date": "2025-02-09",
            "time": "13:00",
            "participants": 7,
        },
    ]
    return mock_tours


# ==================== NOTIFICATIONS ====================
@app.get("/notifications")
def read_notifications():
    # Mock data for testing
    mock_notifications = [
        {
            "id": 1,
            "message": "Guide Ana Costa swapped tour Dolphin Feeding",
            "timestamp": "2025-02-06T14:30:00",
        },
        {
            "id": 2,
            "message": "New booking for Shark Diving received",
            "timestamp": "2025-02-06T13:15:00",
        },
        {
            "id": 3,
            "message": "Guide Liam Brown is unavailable Feb 9",
            "timestamp": "2025-02-06T10:00:00",
        },
    ]
    return mock_notifications


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
                raise HTTPException(
                    status_code=404, detail="Booking not found")

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
                raise HTTPException(
                    status_code=404, detail="Booking not found")

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
    # Mock data for testing
    return {
        "toursToday": 14,
        "customersToday": 45,
        "cancellations": 2,
        "avgRating": "4.9"
    }
