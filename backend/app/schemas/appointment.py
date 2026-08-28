"""
Pydantic schemas for appointment slots and bookings.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SlotOut(BaseModel):
    id: int
    doctor_id: int
    doctor_name: str = ""
    specialty: str = ""
    clinic_name: str = ""
    consultation_fee: float = 0.0
    date: str
    start_time: str
    end_time: str
    status: str

    model_config = {"from_attributes": True}


class BookingRequest(BaseModel):
    slot_id: int = Field(..., description="ID of the appointment slot to book")
    reason_for_visit: Optional[str] = Field(default=None, description="Reason for the visit")
    triage_session_id: Optional[int] = Field(default=None, description="Associated triage session")


class AppointmentOut(BaseModel):
    id: int
    patient_id: int
    slot_id: int
    doctor_name: str = ""
    specialty: str = ""
    clinic_name: str = ""
    date: str = ""
    start_time: str = ""
    end_time: str = ""
    reason_for_visit: Optional[str] = None
    booking_status: str
    triage_session_id: Optional[int] = None
    severity: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
