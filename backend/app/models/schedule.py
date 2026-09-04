"""
Doctor Schedule Template ORM model — recurring daily time windows.
Decoupled from specific dates: availability is computed at query time.
"""
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class DoctorScheduleTemplate(Base):
    """Recurring time slots a doctor is available each working day."""
    __tablename__ = "doctor_schedules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False, index=True)
    start_time = Column(String(10), nullable=False)   # e.g. "09:30 AM"
    end_time = Column(String(10), nullable=False)      # e.g. "10:00 AM"
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    doctor = relationship("Doctor", back_populates="schedules")

    def __repr__(self) -> str:
        return (
            f"<DoctorScheduleTemplate id={self.id} doctor_id={self.doctor_id} "
            f"{self.start_time}-{self.end_time} active={self.is_active}>"
        )
