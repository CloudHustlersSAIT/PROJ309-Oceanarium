from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from ..db import Base


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    type = Column(String, nullable=True)
    quantity_available = Column(Integer, nullable=True)

    schedules = relationship("Schedule", back_populates="resource")
