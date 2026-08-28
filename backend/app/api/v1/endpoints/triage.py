"""
Triage chat endpoint — authenticated multi-turn conversation with the AI agent.
"""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.db.session import get_db
from app.models.triage_session import TriageSession
from app.models.user import User
from app.schemas.triage import BookingDetails, ChatRequest, ChatResponse
from app.services.agent_service import run_triage_agent

router = APIRouter(prefix="/triage", tags=["Triage"])


@router.post("/chat", response_model=ChatResponse)
def triage_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Multi-turn triage chat endpoint.
    Runs the AI agent with RAG context, tool calling, and conversation memory.
    Returns a structured response with optional booking redirect.
    """
    messages_dicts = [{"role": m.role, "content": m.content} for m in request.messages]

    result = run_triage_agent(
        messages=messages_dicts,
        patient_name=current_user.full_name,
        patient_id=current_user.id,
        language=request.language,
    )

    # Extract first user message as chief complaint
    chief_complaint = ""
    for m in request.messages:
        if m.role == "user":
            chief_complaint = m.content
            break

    # Create or update triage session
    severity = result.get("severity")
    triage_session = TriageSession(
        patient_id=current_user.id,
        chief_complaint=chief_complaint,
        severity=severity,
        ai_recommendation=result.get("response_message", ""),
        raw_conversation_history=json.dumps(messages_dicts, ensure_ascii=False),
    )
    db.add(triage_session)
    db.commit()
    db.refresh(triage_session)

    # If booking happened, link triage session to the appointment
    booking = result.get("booking_details")
    if booking and booking.get("appointment_id"):
        from app.models.appointment import Appointment
        appt = (
            db.query(Appointment)
            .filter(Appointment.slot_id == booking["appointment_id"])
            .first()
        )
        if appt and not appt.triage_session_id:
            appt.triage_session_id = triage_session.id
            db.commit()

    booking_details = None
    if booking:
        booking_details = BookingDetails(
            appointment_id=booking.get("appointment_id", 0),
            doctor_name=booking.get("doctor_name", ""),
            specialty=booking.get("specialty", ""),
            date=booking.get("date", ""),
            time=booking.get("time", ""),
            clinic=booking.get("clinic", ""),
        )

    return ChatResponse(
        response_message=result.get("response_message", ""),
        severity=severity,
        action=result.get("action", "NONE"),
        booking_details=booking_details,
    )
