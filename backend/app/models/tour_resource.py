from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from ..db import Base


class TourResource(Base):
    __tablename__ = "tour_resources"

    tour_id = Column(Integer, ForeignKey("tours.id"), primary_key=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), primary_key=True)
    quantity_required = Column(Integer, nullable=False)

    tour = relationship("Tour", back_populates="tour_resources")
    resource = relationship("Resource")
