from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text

from ..db import Base


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    finished_at = Column(DateTime, nullable=True)
    new_count = Column(Integer, default=0)
    changed_count = Column(Integer, default=0)
    cancelled_count = Column(Integer, default=0)
    status = Column(String, nullable=False, default="running")  # running, success, failed
    errors = Column(Text, nullable=True)
