from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..db import Base


class Booking(Base):
    __tablename__ = "bookings"

    booking_id = Column(Integer, primary_key=True, index=True)
    clorian_booking_id = Column(String, nullable=False, unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    tour_id = Column(Integer, ForeignKey("tours.id"), nullable=True)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    customer = relationship("Customer", back_populates="bookings")
    tour = relationship("Tour", back_populates="bookings")
    versions = relationship(
        "BookingVersion",
        back_populates="booking",
        order_by="BookingVersion.id.desc()",
        cascade="all, delete-orphan",
    )

    @property
    def latest_version(self):
        return self.versions[0] if self.versions else None
