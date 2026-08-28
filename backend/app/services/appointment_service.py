"""
Appointment service — atomic slot booking, conflict resolution, and history queries.
"""
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.appointment import Appointment, AppointmentSlot
from app.models.doctor import Doctor
from app.models.triage_session import TriageSession
from app.schemas.appointment import AppointmentOut, SlotOut


def get_available_slots(
    db: Session,
    date: Optional[str] = None,
    specialty: Optional[str] = None,
) -> list[SlotOut]:
    """
    Query available slots with optional date/specialty filters.
    Returns enriched slot info including doctor details.
    """
    query = (
        db.query(AppointmentSlot, Doctor)
        .join(Doctor, AppointmentSlot.doctor_id == Doctor.id)
        .filter(AppointmentSlot.status == "available")
    )
    if date:
        query = query.filter(AppointmentSlot.date == date)
    if specialty:
        query = query.filter(Doctor.specialty.ilike(f"%{specialty}%"))

    query = query.order_by(AppointmentSlot.date, AppointmentSlot.start_time)
    results = query.all()

    return [
        SlotOut(
            id=slot.id,
            doctor_id=slot.doctor_id,
            doctor_name=doctor.name,
            specialty=doctor.specialty,
            clinic_name=doctor.clinic_name,
            consultation_fee=doctor.consultation_fee,
            date=slot.date,
            start_time=slot.start_time,
            end_time=slot.end_time,
            status=slot.status,
        )
        for slot, doctor in results
    ]


def book_slot(
    db: Session,
    patient_id: int,
    slot_id: int,
    triage_session_id: Optional[int] = None,
    reason: Optional[str] = None,
) -> Appointment:
    """
    Atomically book an appointment slot. Raises ValueError on conflicts.
    """
    slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == slot_id).first()
    if not slot:
        raise ValueError(f"Appointment slot #{slot_id} not found.")
    if slot.status != "available":
        raise ValueError(f"Appointment slot #{slot_id} is no longer available.")

    # Check for duplicate booking
    existing = db.query(Appointment).filter(Appointment.slot_id == slot_id).first()
    if existing:
        raise ValueError(f"Slot #{slot_id} is already booked (Appointment #{existing.id}).")

    # Mark slot as booked
    slot.status = "booked"

    # Create the appointment record
    appointment = Appointment(
        patient_id=patient_id,
        slot_id=slot_id,
        triage_session_id=triage_session_id,
        reason_for_visit=reason,
        booking_status="confirmed",
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    db.refresh(slot)
    return appointment


def get_user_appointments(db: Session, patient_id: int) -> list[AppointmentOut]:
    """Get all appointments for a patient, enriched with doctor/slot details."""
    results = (
        db.query(Appointment, AppointmentSlot, Doctor)
        .join(AppointmentSlot, Appointment.slot_id == AppointmentSlot.id)
        .join(Doctor, AppointmentSlot.doctor_id == Doctor.id)
        .outerjoin(TriageSession, Appointment.triage_session_id == TriageSession.id)
        .filter(Appointment.patient_id == patient_id)
        .order_by(Appointment.created_at.desc())
        .all()
    )

    appointments = []
    for appt, slot, doctor in results:
        # Get triage severity if linked
        severity = None
        if appt.triage_session_id:
            ts = db.query(TriageSession).filter(TriageSession.id == appt.triage_session_id).first()
            if ts:
                severity = ts.severity

        appointments.append(
            AppointmentOut(
                id=appt.id,
                patient_id=appt.patient_id,
                slot_id=appt.slot_id,
                doctor_name=doctor.name,
                specialty=doctor.specialty,
                clinic_name=doctor.clinic_name,
                date=slot.date,
                start_time=slot.start_time,
                end_time=slot.end_time,
                reason_for_visit=appt.reason_for_visit,
                booking_status=appt.booking_status,
                triage_session_id=appt.triage_session_id,
                severity=severity,
                created_at=appt.created_at,
            )
        )
    return appointments


def cancel_appointment(db: Session, appointment_id: int, patient_id: int) -> Appointment:
    """Cancel an appointment — validates ownership, restores slot availability."""
    appt = (
        db.query(Appointment)
        .filter(Appointment.id == appointment_id, Appointment.patient_id == patient_id)
        .first()
    )
    if not appt:
        raise ValueError("Appointment not found or not owned by this patient.")
    if appt.booking_status == "cancelled":
        raise ValueError("Appointment is already cancelled.")

    appt.booking_status = "cancelled"

    # Restore slot availability
    slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == appt.slot_id).first()
    if slot:
        slot.status = "available"

    db.commit()
    db.refresh(appt)
    return appt
