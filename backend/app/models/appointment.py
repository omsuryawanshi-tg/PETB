"""
Appointment-related ORM models — slots and bookings (normalized 3NF).
"""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base


class AppointmentSlot(Base):
    """Available time slots for doctors. Status transitions: available → booked → cancelled."""
    __tablename__ = "appointment_slots"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False, index=True)
    date = Column(String(10), nullable=False)       # YYYY-MM-DD
    start_time = Column(String(5), nullable=False)   # HH:MM (24h)
    end_time = Column(String(5), nullable=False)     # HH:MM (24h)
    status = Column(String(20), nullable=False, default="available")  # available | booked | cancelled

    # Relationships
    doctor = relationship("Doctor", back_populates="slots")
    appointment = relationship("Appointment", back_populates="slot", uselist=False)

    def __repr__(self) -> str:
        return f"<AppointmentSlot id={self.id} doctor_id={self.doctor_id} {self.date} {self.start_time}-{self.end_time} [{self.status}]>"


class Appointment(Base):
    """Booked appointments linking a patient to a specific slot."""
    __tablename__ = "appointments"
    __table_args__ = (
        UniqueConstraint("slot_id", name="uq_appointment_slot"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    slot_id = Column(Integer, ForeignKey("appointment_slots.id"), nullable=False, unique=True)
    triage_session_id = Column(Integer, ForeignKey("triage_sessions.id"), nullable=True)
    reason_for_visit = Column(Text, nullable=True)
    booking_status = Column(String(20), nullable=False, default="confirmed")  # confirmed | completed | cancelled
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    patient = relationship("User", back_populates="appointments")
    slot = relationship("AppointmentSlot", back_populates="appointment")
    triage_session = relationship("TriageSession", back_populates="appointment")

    def __repr__(self) -> str:
        return f"<Appointment id={self.id} patient_id={self.patient_id} slot_id={self.slot_id} [{self.booking_status}]>"
