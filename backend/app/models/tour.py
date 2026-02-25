from sqlalchemy import Column, Date, ForeignKey, Integer, String, Time
from sqlalchemy.orm import relationship

from ..db import Base


class Tour(Base):
    __tablename__ = "tours"

    id = Column(Integer, primary_key=True, index=True)
    clorian_booking_id = Column(String, nullable=False, unique=True, index=True)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    required_expertise = Column(String, nullable=True)
    required_category = Column(String, nullable=True)
    requested_language_code = Column(String, nullable=True)
    status = Column(String, nullable=False, default="pending")  # pending, assigned, unassigned, cancelled
    assigned_guide_id = Column(Integer, ForeignKey("guides.id"), nullable=True)

    assigned_guide = relationship("Guide", back_populates="assigned_tours")
    assignment_logs = relationship("TourAssignmentLog", back_populates="tour", cascade="all, delete-orphan")
