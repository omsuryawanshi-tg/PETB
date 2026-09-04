"""
Triage chat endpoint — authenticated multi-turn conversation with the AI agent.
Returns structured ChatResponse with optional slot cards and booking redirect.
"""
import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.db.session import get_db
from app.models.appointment import Appointment
from app.models.triage_session import TriageSession
from app.models.user import User
from app.schemas.triage import BookingDetails, ChatRequest, ChatResponse, SlotItem
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
    Returns a structured response with optional slot cards or booking redirect.
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

    # Create triage session record
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
        appt = (
            db.query(Appointment)
            .filter(Appointment.id == booking["appointment_id"])
            .first()
        )
        if appt and not appt.triage_session_id:
            appt.triage_session_id = triage_session.id
            db.commit()

    # Build structured response
    booking_details = None
    if booking:
        booking_details = BookingDetails(
            appointment_id=booking.get("appointment_id", 0),
            doctor_name=booking.get("doctor_name", ""),
            specialty=booking.get("specialty", ""),
            clinic_name=booking.get("clinic_name", ""),
            date=booking.get("date", ""),
            time_slot=booking.get("time_slot", ""),
            fee=booking.get("fee", 0.0),
        )

    # Build structured slot items
    available_slots = []
    raw_slots = result.get("available_slots", [])
    for s in raw_slots:
        available_slots.append(
            SlotItem(
                doctor_id=s.get("doctor_id", 0),
                doctor_name=s.get("doctor_name", ""),
                specialty=s.get("specialty", ""),
                clinic_name=s.get("clinic", s.get("clinic_name", "")),
                fee=s.get("consultation_fee", s.get("fee", 0.0)),
                rating=s.get("rating", 0.0),
                date=s.get("date", ""),
                time_slot=s.get("time_slot", ""),
            )
        )

    return ChatResponse(
        response_message=result.get("response_message", ""),
        severity=severity,
        action=result.get("action", "NONE"),
        available_slots=available_slots,
        booking_details=booking_details,
    )
