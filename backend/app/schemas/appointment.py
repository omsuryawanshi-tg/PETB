"""
Pydantic schemas for appointment slots and bookings — aligned with new schema (no AppointmentSlot).
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SlotOut(BaseModel):
    """Available slot computed from schedule templates minus booked appointments."""
    doctor_id: int
    doctor_name: str = ""
    specialty: str = ""
    clinic_name: str = ""
    consultation_fee: float = 0.0
    rating: float = 0.0
    date: str
    time_slot: str  # e.g. "09:30 AM - 10:00 AM"

    model_config = {"from_attributes": True}


class BookingRequest(BaseModel):
    """Request body for booking an appointment (no more slot_id)."""
    doctor_id: int = Field(..., description="ID of the doctor to book with")
    date: str = Field(..., description="Appointment date (YYYY-MM-DD)")
    time_slot: str = Field(..., description="Time slot string, e.g. '09:30 AM - 10:00 AM'")
    reason_for_visit: Optional[str] = Field(default=None, description="Reason for the visit")
    triage_session_id: Optional[int] = Field(default=None, description="Associated triage session")


class AppointmentOut(BaseModel):
    """Appointment details returned to the frontend."""
    id: int
    patient_id: Optional[int] = None
    doctor_id: int
    doctor_name: str = ""
    specialty: str = ""
    clinic_name: str = ""
    consultation_fee: float = 0.0
    date: str = ""
    time_slot: str = ""
    reason_for_visit: Optional[str] = None
    booking_status: str = "confirmed"
    triage_session_id: Optional[int] = None
    severity: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
