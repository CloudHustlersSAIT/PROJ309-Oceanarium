from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..db import Base


class Booking(Base):
    __tablename__ = "bookings"

    booking_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String, nullable=False)
    tour_id = Column(Integer, ForeignKey("tours.id"), nullable=False)
    date = Column(Date, nullable=False)
    adult_tickets = Column(Integer, nullable=False, default=0)
    child_tickets = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default="confirmed")
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    tour = relationship("Tour")
