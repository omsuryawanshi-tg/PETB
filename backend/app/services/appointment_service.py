"""
Appointment service — dynamic availability computation, atomic booking, history, and cancellation.
Uses DoctorScheduleTemplate + Appointment (no more AppointmentSlot).
"""
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.schedule import DoctorScheduleTemplate
from app.models.triage_session import TriageSession
from app.schemas.appointment import AppointmentOut, SlotOut


def get_available_slots(
    db: Session,
    target_date: Optional[str] = None,
    specialty: Optional[str] = None,
) -> list[SlotOut]:
    """
    Compute available slots by taking all active schedule templates and subtracting
    existing appointments for the target date(s).
    If no date is given, defaults to the next 7 weekdays.
    """
    # Determine which dates to check
    if target_date:
        dates = [target_date]
    else:
        today = date.today()
        dates = []
        for offset in range(1, 10):
            d = today + timedelta(days=offset)
            if d.weekday() != 6:  # skip Sundays
                dates.append(d.strftime("%Y-%m-%d"))
            if len(dates) >= 7:
                break

    # Get all active schedule templates with doctor info
    query = (
        db.query(DoctorScheduleTemplate, Doctor)
        .join(Doctor, DoctorScheduleTemplate.doctor_id == Doctor.id)
        .filter(DoctorScheduleTemplate.is_active == True)
    )
    if specialty:
        query = query.filter(Doctor.specialty.ilike(f"%{specialty}%"))

    templates = query.all()

    # Get existing non-cancelled appointments for the target dates
    existing = (
        db.query(Appointment)
        .filter(
            Appointment.date.in_(dates),
            Appointment.status != "cancelled",
        )
        .all()
    )
    booked = {(a.doctor_id, a.date, a.time_slot) for a in existing}

    # Build available slots
    results = []
    for check_date in dates:
        for template, doctor in templates:
            time_slot = f"{template.start_time} - {template.end_time}"
            if (doctor.id, check_date, time_slot) not in booked:
                results.append(
                    SlotOut(
                        doctor_id=doctor.id,
                        doctor_name=doctor.name,
                        specialty=doctor.specialty,
                        clinic_name=doctor.clinic_name,
                        consultation_fee=doctor.consultation_fee,
                        rating=doctor.rating,
                        date=check_date,
                        time_slot=time_slot,
                    )
                )

    # Sort by date, then time
    results.sort(key=lambda s: (s.date, s.time_slot, s.doctor_name))
    return results


def book_slot(
    db: Session,
    patient_id: int,
    doctor_id: int,
    target_date: str,
    time_slot: str,
    triage_session_id: Optional[int] = None,
    reason: Optional[str] = None,
) -> Appointment:
    """
    Atomically book an appointment. Raises ValueError on conflicts.
    Validates:
    1. Doctor exists
    2. Time slot is in the doctor's active schedule
    3. No conflicting appointment exists
    """
    # Verify doctor
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise ValueError(f"Doctor #{doctor_id} not found.")

    # Verify schedule template exists
    parts = time_slot.split(" - ")
    if len(parts) != 2:
        raise ValueError(f"Invalid time_slot format: '{time_slot}'.")

    start_time, end_time = parts[0].strip(), parts[1].strip()
    template = (
        db.query(DoctorScheduleTemplate)
        .filter(
            DoctorScheduleTemplate.doctor_id == doctor_id,
            DoctorScheduleTemplate.start_time == start_time,
            DoctorScheduleTemplate.end_time == end_time,
            DoctorScheduleTemplate.is_active == True,
        )
        .first()
    )
    if not template:
        raise ValueError(f"Time slot '{time_slot}' is not in Dr. {doctor.name}'s active schedule.")

    # Check for duplicate booking
    existing = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.date == target_date,
            Appointment.time_slot == time_slot,
            Appointment.status != "cancelled",
        )
        .first()
    )
    if existing:
        raise ValueError(f"This slot is already booked (Appointment #{existing.id}).")

    # Create the appointment
    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        date=target_date,
        time_slot=time_slot,
        status="confirmed",
        triage_session_id=triage_session_id,
        reason_for_visit=reason,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def get_user_appointments(db: Session, patient_id: int) -> list[AppointmentOut]:
    """Get all appointments for a patient, enriched with doctor details."""
    results = (
        db.query(Appointment, Doctor)
        .join(Doctor, Appointment.doctor_id == Doctor.id)
        .filter(Appointment.patient_id == patient_id)
        .order_by(Appointment.created_at.desc())
        .all()
    )

    appointments = []
    for appt, doctor in results:
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
                doctor_id=appt.doctor_id,
                doctor_name=doctor.name,
                specialty=doctor.specialty,
                clinic_name=doctor.clinic_name,
                consultation_fee=doctor.consultation_fee,
                date=appt.date,
                time_slot=appt.time_slot,
                reason_for_visit=appt.reason_for_visit,
                booking_status=appt.status,
                triage_session_id=appt.triage_session_id,
                severity=severity,
                created_at=appt.created_at,
            )
        )
    return appointments


def cancel_appointment(db: Session, appointment_id: int, patient_id: int) -> Appointment:
    """Cancel an appointment — validates ownership."""
    appt = (
        db.query(Appointment)
        .filter(Appointment.id == appointment_id, Appointment.patient_id == patient_id)
        .first()
    )
    if not appt:
        raise ValueError("Appointment not found or not owned by this patient.")
    if appt.status == "cancelled":
        raise ValueError("Appointment is already cancelled.")

    appt.status = "cancelled"
    db.commit()
    db.refresh(appt)
    return appt
