from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..db import Base


class Survey(Base):
    __tablename__ = "surveys"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    guide_id = Column(Integer, ForeignKey("guides.id"), nullable=False)
    booking_version_id = Column(
        Integer, ForeignKey("booking_versions.id"), nullable=False
    )
    comment = Column(String, nullable=True)
    rating = Column(Integer, nullable=False)

    customer = relationship("Customer", back_populates="surveys")
    guide = relationship("Guide", back_populates="surveys")
    booking_version = relationship("BookingVersion", back_populates="surveys")
