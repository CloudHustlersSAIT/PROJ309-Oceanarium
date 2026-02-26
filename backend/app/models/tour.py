from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from ..db import Base


class Tour(Base):
    __tablename__ = "tours"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    description = Column(String, nullable=True)
    duration = Column(Integer, nullable=True)

    costs = relationship("Cost", back_populates="tour", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="tour")
    tour_resources = relationship("TourResource", back_populates="tour", cascade="all, delete-orphan")
    assignment_logs = relationship("TourAssignmentLog", back_populates="tour", cascade="all, delete-orphan")
    guides = relationship("Guide", secondary="guide_tour_types", back_populates="tour_types")
