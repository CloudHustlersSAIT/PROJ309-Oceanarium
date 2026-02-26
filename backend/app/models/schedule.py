from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from ..db import Base


class Schedule(Base):
    __tablename__ = "schedule"

    id = Column(Integer, primary_key=True, index=True)
    booking_version_id = Column(
        Integer, ForeignKey("booking_versions.id"), nullable=False
    )
    guide_id = Column(Integer, ForeignKey("guides.id"), nullable=False)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    booking_version = relationship("BookingVersion", back_populates="schedules")
    guide = relationship("Guide", back_populates="schedules")
    resource = relationship("Resource", back_populates="schedules")
