"""
Appointment endpoints — slot listing, booking, history, and cancellation.
Updated for new schema: no more AppointmentSlot, uses doctor_id + date + time_slot.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.appointment import AppointmentOut, BookingRequest, SlotOut
from app.services.appointment_service import (
    book_slot,
    cancel_appointment,
    get_available_slots,
    get_user_appointments,
)

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.get("/slots", response_model=list[SlotOut])
def list_available_slots(
    date: Optional[str] = Query(default=None, description="Filter by date (YYYY-MM-DD)"),
    specialty: Optional[str] = Query(default=None, description="Filter by doctor specialty"),
    db: Session = Depends(get_db),
):
    """List available appointment slots, computed dynamically from schedule templates."""
    return get_available_slots(db, target_date=date, specialty=specialty)


@router.post("/book", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def book_appointment(
    payload: BookingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Book an appointment for the authenticated patient using doctor_id + date + time_slot."""
    try:
        appt = book_slot(
            db=db,
            patient_id=current_user.id,
            doctor_id=payload.doctor_id,
            target_date=payload.date,
            time_slot=payload.time_slot,
            triage_session_id=payload.triage_session_id,
            reason=payload.reason_for_visit,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Return enriched appointment
    appointments = get_user_appointments(db, current_user.id)
    for a in appointments:
        if a.id == appt.id:
            return a

    # Fallback (shouldn't reach here)
    raise HTTPException(status_code=500, detail="Booking succeeded but could not retrieve details.")


@router.get("/my", response_model=list[AppointmentOut])
def my_appointments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the authenticated patient's appointment history."""
    return get_user_appointments(db, current_user.id)


@router.delete("/{appointment_id}/cancel", status_code=status.HTTP_200_OK)
def cancel_booking(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel an existing appointment."""
    try:
        appt = cancel_appointment(db, appointment_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"message": f"Appointment #{appt.id} has been cancelled.", "success": True}
