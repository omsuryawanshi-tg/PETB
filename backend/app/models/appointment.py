"""
Appointment ORM model — booked visits linking a patient to a doctor on a specific date/time.
Availability is computed dynamically from DoctorScheduleTemplate minus existing appointments.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Appointment(Base):
    """Booked appointment — ties a patient to a doctor at a specific date + time slot."""
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False, index=True)
    date = Column(String(10), nullable=False)           # YYYY-MM-DD
    time_slot = Column(String(30), nullable=False)       # e.g. "09:30 AM - 10:00 AM"
    status = Column(String(20), nullable=False, default="confirmed")  # confirmed | completed | cancelled
    triage_session_id = Column(Integer, ForeignKey("triage_sessions.id"), nullable=True)
    reason_for_visit = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    patient = relationship("User", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    triage_session = relationship("TriageSession", back_populates="appointment")

    def __repr__(self) -> str:
        return (
            f"<Appointment id={self.id} patient_id={self.patient_id} "
            f"doctor_id={self.doctor_id} {self.date} {self.time_slot} [{self.status}]>"
        )
