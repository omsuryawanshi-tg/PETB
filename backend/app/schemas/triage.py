"""
Pydantic schemas for triage chat: request, response, slot items, and booking details.
"""
from typing import List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message text content")


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(
        ...,
        min_length=1,
        description="Multi-turn conversation history",
    )
    language: str = Field(default="en", description="Response language code (en/hi)")


class SlotItem(BaseModel):
    """A single available appointment slot — sent as structured data for frontend card rendering."""
    doctor_id: int
    doctor_name: str
    specialty: str
    clinic_name: str
    fee: float
    rating: float
    date: str          # YYYY-MM-DD
    time_slot: str     # e.g. "09:30 AM - 10:00 AM"


class BookingDetails(BaseModel):
    """Confirmed booking information — triggers frontend redirect to confirmation page."""
    appointment_id: int = Field(..., description="Booked appointment ID")
    doctor_name: str = Field(default="", description="Doctor's display name")
    specialty: str = Field(default="", description="Doctor's specialty")
    clinic_name: str = Field(default="", description="Clinic name")
    date: str = Field(default="", description="Appointment date (YYYY-MM-DD)")
    time_slot: str = Field(default="", description="Appointment time slot")
    fee: float = Field(default=0.0, description="Consultation fee")


class ChatResponse(BaseModel):
    """Structured response from the triage agent to the frontend."""
    response_message: str = Field(..., description="Assistant reply for the patient")
    severity: Optional[str] = Field(default="low", description="Assessed severity level")
    action: str = Field(
        default="NONE",
        description="NONE, SHOW_SLOTS, or REDIRECT_TO_CONFIRMATION",
    )
    available_slots: List[SlotItem] = Field(
        default=[],
        description="Available slots when action is SHOW_SLOTS",
    )
    booking_details: Optional[BookingDetails] = Field(
        default=None,
        description="Present when action is REDIRECT_TO_CONFIRMATION",
    )
