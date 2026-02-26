from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from ..db import Base


class BookingVersion(Base):
    __tablename__ = "booking_versions"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.booking_id"), nullable=False)
    hash = Column(String(64), nullable=False)
    status = Column(String(50), nullable=False)
    adult_tickets = Column(Integer, nullable=False)
    child_tickets = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    received_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    valid_from = Column(DateTime, nullable=False)
    poll_execution_id = Column(
        Integer, ForeignKey("poll_execution.id"), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("booking_id", "hash", name="uq_booking_hash"),
    )

    booking = relationship("Booking", back_populates="versions")
    poll_execution = relationship("PollExecution", back_populates="versions")
    schedules = relationship("Schedule", back_populates="booking_version")
    surveys = relationship("Survey", back_populates="booking_version")
