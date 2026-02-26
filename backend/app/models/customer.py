from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from ..db import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)

    bookings = relationship("Booking", back_populates="customer")
    surveys = relationship("Survey", back_populates="customer")
