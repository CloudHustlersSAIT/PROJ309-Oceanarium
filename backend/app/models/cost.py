from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from ..db import Base


class Cost(Base):
    __tablename__ = "cost"

    id = Column(Integer, primary_key=True, index=True)
    tour_id = Column(Integer, ForeignKey("tours.id"), nullable=False)
    ticket_type = Column(String(20), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime, nullable=False)

    tour = relationship("Tour", back_populates="costs")
