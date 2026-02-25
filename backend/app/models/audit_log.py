from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..db import Base


class TourAssignmentLog(Base):
    __tablename__ = "tour_assignment_logs"

    id = Column(Integer, primary_key=True, index=True)
    tour_id = Column(Integer, ForeignKey("tours.id"), nullable=False)
    guide_id = Column(Integer, ForeignKey("guides.id"), nullable=True)
    assigned_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    assigned_by = Column(String, nullable=True)  # null for auto, admin email for manual
    assignment_type = Column(String, nullable=False)  # "auto" or "manual"
    action = Column(String, nullable=False)  # "assigned", "released", "reassigned"

    tour = relationship("Tour", back_populates="assignment_logs")
    guide = relationship("Guide")
