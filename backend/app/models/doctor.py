"""
Doctor ORM model — medical professionals with specialties.
"""
from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    specialty = Column(String(100), nullable=False)
    clinic_name = Column(String(200), nullable=False)
    consultation_fee = Column(Float, nullable=False, default=500.0)
    rating = Column(Float, nullable=False, default=4.0)

    # Relationships
    slots = relationship("AppointmentSlot", back_populates="doctor", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Doctor id={self.id} name={self.name!r} specialty={self.specialty!r}>"
