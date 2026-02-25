from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from ..db import Base

guide_language = Table(
    "guide_languages",
    Base.metadata,
    Column("guide_id", Integer, ForeignKey("guides.id"), primary_key=True),
    Column("language_id", Integer, ForeignKey("languages.id"), primary_key=True),
)

guide_expertise = Table(
    "guide_expertises",
    Base.metadata,
    Column("guide_id", Integer, ForeignKey("guides.id"), primary_key=True),
    Column("expertise_id", Integer, ForeignKey("expertises.id"), primary_key=True),
)


class Guide(Base):
    __tablename__ = "guides"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean, default=True, nullable=False)

    languages = relationship("Language", secondary=guide_language, back_populates="guides")
    expertises = relationship("Expertise", secondary=guide_expertise, back_populates="guides")
    availability_pattern = relationship(
        "AvailabilityPattern", back_populates="guide", uselist=False, cascade="all, delete-orphan"
    )
    assigned_tours = relationship("Tour", back_populates="assigned_guide")


class Language(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)

    guides = relationship("Guide", secondary=guide_language, back_populates="languages")


class Expertise(Base):
    __tablename__ = "expertises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)

    guides = relationship("Guide", secondary=guide_expertise, back_populates="expertises")
