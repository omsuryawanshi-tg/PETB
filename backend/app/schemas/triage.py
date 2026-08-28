"""
Pydantic schemas for triage chat: request, response, and booking details.
"""
from typing import Optional

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


class BookingDetails(BaseModel):
    appointment_id: int = Field(..., description="Booked appointment ID")
    doctor_name: str = Field(default="", description="Doctor's display name")
    specialty: str = Field(default="", description="Doctor's specialty")
    date: str = Field(default="", description="Appointment date (YYYY-MM-DD)")
    time: str = Field(default="", description="Appointment start time")
    clinic: str = Field(default="", description="Clinic name")


class ChatResponse(BaseModel):
    response_message: str = Field(..., description="Assistant reply for the patient")
    severity: Optional[str] = Field(default=None, description="Assessed severity level")
    action: str = Field(
        default="NONE",
        description="NONE or REDIRECT_TO_CONFIRMATION after successful booking",
    )
    booking_details: Optional[BookingDetails] = Field(
        default=None,
        description="Present when action is REDIRECT_TO_CONFIRMATION",
    )
