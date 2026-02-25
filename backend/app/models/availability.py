from sqlalchemy import Column, Date, ForeignKey, Integer, String, Time
from sqlalchemy.orm import relationship

from ..db import Base


class AvailabilityPattern(Base):
    __tablename__ = "availability_patterns"

    id = Column(Integer, primary_key=True, index=True)
    guide_id = Column(Integer, ForeignKey("guides.id"), nullable=False, unique=True)
    timezone = Column(String, nullable=False, default="UTC")

    guide = relationship("Guide", back_populates="availability_pattern")
    slots = relationship("AvailabilitySlot", back_populates="pattern", cascade="all, delete-orphan")
    exceptions = relationship(
        "AvailabilityException", back_populates="pattern", cascade="all, delete-orphan"
    )


class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"

    id = Column(Integer, primary_key=True, index=True)
    pattern_id = Column(Integer, ForeignKey("availability_patterns.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday ... 6=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    pattern = relationship("AvailabilityPattern", back_populates="slots")


class AvailabilityException(Base):
    __tablename__ = "availability_exceptions"

    id = Column(Integer, primary_key=True, index=True)
    pattern_id = Column(Integer, ForeignKey("availability_patterns.id"), nullable=False)
    date = Column(Date, nullable=False)
    type = Column(String, nullable=False)  # "blocked", "note"
    reason = Column(String, nullable=True)

    pattern = relationship("AvailabilityPattern", back_populates="exceptions")
