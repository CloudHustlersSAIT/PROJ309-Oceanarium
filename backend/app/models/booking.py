from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Time
from sqlalchemy.orm import relationship

from ..db import Base


class Booking(Base):
    __tablename__ = "bookings"

    booking_id = Column(Integer, primary_key=True, index=True)
    clorian_booking_id = Column(String, nullable=False, unique=True, index=True)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    required_expertise = Column(String, nullable=True)
    required_category = Column(String, nullable=True)
    requested_language_code = Column(String, nullable=True)
    customer_id = Column(String, nullable=True)
    adult_tickets = Column(Integer, nullable=False, default=0)
    child_tickets = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default="pending")
    tour_id = Column(Integer, ForeignKey("tours.id"), nullable=True)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    tour = relationship("Tour", back_populates="booking")
