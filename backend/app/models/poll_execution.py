from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from ..db import Base


class PollExecution(Base):
    __tablename__ = "poll_execution"

    id = Column(Integer, primary_key=True, index=True)
    window_start = Column(DateTime, nullable=False)
    window_end = Column(DateTime, nullable=False)
    executed_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    status = Column(String(50), nullable=False)

    versions = relationship("BookingVersion", back_populates="poll_execution")
