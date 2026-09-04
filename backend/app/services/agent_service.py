"""
Multi-turn conversational triage agent with tool calling via local Ollama LLM.
Refactored to use DoctorScheduleTemplate + Appointment (no more AppointmentSlot).
Fixes false "already booked" bugs by computing availability dynamically.
"""
import json
import re
from datetime import datetime, date, timedelta
from typing import Any, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.schedule import DoctorScheduleTemplate
from app.models.triage_session import TriageSession
from app.services.rag_service import get_relevant_context


SYSTEM_PROMPT_TEMPLATE = """You are an empathetic AI medical triage nurse helping patients assess symptoms and book appointments when needed.

PATIENT NAME: {patient_name}
RESPONSE LANGUAGE: {language}

CLINICAL REFERENCE GUIDELINES (use these to assess severity):
{context}

YOUR WORKFLOW:
1. Listen carefully to the patient's symptoms. Be warm, calm, and clear.
2. Assess severity using the clinical guidelines:
   - LOW: mild symptoms, self-care advised
   - MEDIUM: needs doctor within 24-48h
   - HIGH: needs urgent care today
   - EMERGENCY: needs immediate ER / call 911
3. If severity is LOW: give self-care advice. Do NOT push booking unless the patient asks.
4. If severity is MEDIUM, HIGH, or approaching EMERGENCY (but not immediate 911): recommend seeing a doctor and ask for their preferred day or date.
5. When the patient specifies a day or date, call the check_available_slots tool.
6. Present the slot results briefly — say something like "I found available slots for that day, please choose one from the options shown below." Do NOT list the slots in your message text — the frontend will display them as interactive cards.
7. When the patient selects a slot (by mentioning a doctor name, time, or saying "book slot 1"), call book_appointment with the correct doctor_id, date, and time_slot.
8. After a successful booking, confirm the appointment warmly and mention they will be redirected for confirmation.

EMERGENCY RULE:
If symptoms suggest a true emergency (thunderclap headache, chest pain with shortness of breath, stroke signs, unconsciousness), urge them to call emergency services / go to the ER immediately. Do not book a routine appointment.

TOOL RULES:
- Call check_available_slots only when the user has indicated a preferred day or date.
- Call book_appointment only when the user has clearly chosen a specific slot (by doctor name + time, or by slot number).
- Never invent slots — only use tool results.
- Do NOT list slots as text — just say "here are the available slots" and the frontend shows cards.

SEVERITY ASSESSMENT:
After each response, mentally note the severity level. Include severity assessment in your thinking but respond naturally to the patient.

After tools finish (or if no tools are needed), reply to the patient in natural language in {language}. Do not wrap your reply in JSON or markdown code fences.
"""


def _resolve_date(day_or_date: str) -> list[str]:
    """Resolve a user's day/date text to a list of YYYY-MM-DD date strings."""
    query = day_or_date.strip().lower()
    today = date.today()

    # Handle "today", "tomorrow" and Hindi equivalents
    if query in ("today", "aaj", "आज"):
        return [today.strftime("%Y-%m-%d")]
    if query in ("tomorrow", "kal", "कल"):
        return [(today + timedelta(days=1)).strftime("%Y-%m-%d")]

    # Try parsing as YYYY-MM-DD directly
    try:
        dt = datetime.strptime(query, "%Y-%m-%d").date()
        return [dt.strftime("%Y-%m-%d")]
    except ValueError:
        pass

    # Try common date formats
    for fmt in ("%B %d", "%b %d", "%d %B", "%d %b", "%B %d, %Y", "%m/%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            dt = datetime.strptime(query, fmt).date()
            # If no year in format, use current year (or next year if date already passed)
            if "%Y" not in fmt:
                dt = dt.replace(year=today.year)
                if dt < today:
                    dt = dt.replace(year=today.year + 1)
            return [dt.strftime("%Y-%m-%d")]
        except ValueError:
            continue

    # Try matching day name (e.g. "friday", "monday") — find the next occurrence within 7 days
    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for i, name in enumerate(day_names):
        if query == name or query == name[:3] or name.startswith(query):
            # Find the next occurrence of this weekday
            days_ahead = i - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            target = today + timedelta(days=days_ahead)
            return [target.strftime("%Y-%m-%d")]

    # Fallback: return next 3 days
    return [(today + timedelta(days=d)).strftime("%Y-%m-%d") for d in range(1, 4)]


@tool
def check_available_slots(day_or_date: str) -> str:
    """Query available appointment slots for a day name or date.
    Use when the patient specifies a preferred day or date (e.g. 'Friday', '2026-09-01', 'tomorrow').
    Returns available slots with doctor names, specialties, dates, times, and clinics.
    """
    db = SessionLocal()
    try:
        dates = _resolve_date(day_or_date)

        # Get all active schedule templates with doctor info
        templates = (
            db.query(DoctorScheduleTemplate, Doctor)
            .join(Doctor, DoctorScheduleTemplate.doctor_id == Doctor.id)
            .filter(DoctorScheduleTemplate.is_active == True)
            .all()
        )

        # Get existing non-cancelled appointments for the target dates
        existing_appointments = (
            db.query(Appointment)
            .filter(
                Appointment.date.in_(dates),
                Appointment.status != "cancelled",
            )
            .all()
        )

        # Build a set of booked (doctor_id, date, time_slot) tuples
        booked = {
            (appt.doctor_id, appt.date, appt.time_slot)
            for appt in existing_appointments
        }

        # Compute available slots
        slots = []
        for target_date in dates:
            # Skip Sundays
            dt = datetime.strptime(target_date, "%Y-%m-%d").date()
            if dt.weekday() == 6:
                continue

            for template, doctor in templates:
                time_slot = f"{template.start_time} - {template.end_time}"
                if (doctor.id, target_date, time_slot) not in booked:
                    slots.append({
                        "doctor_id": doctor.id,
                        "doctor_name": doctor.name,
                        "specialty": doctor.specialty,
                        "clinic": doctor.clinic_name,
                        "consultation_fee": doctor.consultation_fee,
                        "rating": doctor.rating,
                        "date": target_date,
                        "time_slot": time_slot,
                    })

        if not slots:
            # Show which dates have no availability
            return json.dumps({
                "found": False,
                "message": f"No available slots found for '{day_or_date}'.",
                "hint": "The patient can try a different day.",
            })

        # Sort by date, then doctor name, then time
        slots.sort(key=lambda s: (s["date"], s["doctor_name"], s["time_slot"]))

        return json.dumps({"found": True, "count": len(slots), "slots": slots})
    except Exception as e:
        return json.dumps({"found": False, "error": str(e)})
    finally:
        db.close()


@tool
def book_appointment(doctor_id: int, date: str, time_slot: str) -> str:
    """Book an appointment with a specific doctor on a specific date and time slot.
    Use when the patient has selected a specific slot. Atomically checks availability and creates the appointment.
    Args:
        doctor_id: The doctor's ID
        date: The appointment date in YYYY-MM-DD format
        time_slot: The time slot string, e.g. '09:30 AM - 10:00 AM'
    """
    db = SessionLocal()
    try:
        # Verify the doctor exists
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doctor:
            return json.dumps({"success": False, "error": f"Doctor #{doctor_id} not found."})

        # Verify this time slot is in the doctor's active schedule
        parts = time_slot.split(" - ")
        if len(parts) != 2:
            return json.dumps({"success": False, "error": f"Invalid time_slot format: '{time_slot}'."})

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
            return json.dumps({
                "success": False,
                "error": f"Time slot '{time_slot}' is not in Dr. {doctor.name}'s schedule.",
            })

        # Atomic check: is this slot already booked?
        existing = (
            db.query(Appointment)
            .filter(
                Appointment.doctor_id == doctor_id,
                Appointment.date == date,
                Appointment.time_slot == time_slot,
                Appointment.status != "cancelled",
            )
            .first()
        )
        if existing:
            return json.dumps({
                "success": False,
                "error": f"This slot is already booked (Appointment #{existing.id}).",
            })

        # Create the appointment (patient_id will be set by the API layer)
        appointment = Appointment(
            doctor_id=doctor_id,
            date=date,
            time_slot=time_slot,
            status="confirmed",
        )
        db.add(appointment)
        db.commit()
        db.refresh(appointment)

        confirmation = {
            "success": True,
            "appointment_id": appointment.id,
            "doctor_id": doctor.id,
            "doctor_name": doctor.name,
            "specialty": doctor.specialty,
            "clinic_name": doctor.clinic_name,
            "date": date,
            "time_slot": time_slot,
            "fee": doctor.consultation_fee,
        }
        return json.dumps(confirmation)
    except Exception as e:
        db.rollback()
        return json.dumps({"success": False, "error": str(e)})
    finally:
        db.close()


TOOLS = [check_available_slots, book_appointment]
TOOL_MAP = {t.name: t for t in TOOLS}


def _latest_user_text(messages: list[dict]) -> str:
    """Extract the latest user message text from conversation history."""
    for msg in reversed(messages):
        if msg.get("role") == "user" and msg.get("content"):
            return str(msg["content"])
    return ""


def _to_langchain_messages(system_prompt: str, messages: list[dict]) -> list:
    """Convert frontend message dicts to LangChain message objects."""
    lc_messages: list = [SystemMessage(content=system_prompt)]
    for msg in messages:
        role = (msg.get("role") or "").lower()
        content = str(msg.get("content") or "")
        if role == "user":
            lc_messages.append(HumanMessage(content=content))
        elif role in ("assistant", "ai"):
            lc_messages.append(AIMessage(content=content))
        elif role == "system":
            lc_messages.append(SystemMessage(content=content))
    return lc_messages


def _extract_text(content: Any) -> str:
    """Extract plain text from various LangChain content formats."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "\n".join(parts).strip()
    return str(content).strip()


def _try_parse_json_blob(text: str) -> Optional[dict]:
    """Attempt to parse JSON from model output (sometimes wrapped in code fences)."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\n?```$", "", cleaned)
        cleaned = cleaned.strip()
    try:
        data = json.loads(cleaned)
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, TypeError):
        return None


def _detect_severity(text: str) -> Optional[str]:
    """Heuristic severity detection from the AI response text."""
    lower = text.lower()
    if any(w in lower for w in ["emergency", "911", "er immediately", "call ambulance", "आपातकालीन"]):
        return "emergency"
    if any(w in lower for w in ["high severity", "urgent", "high risk", "see a doctor today", "तुरंत"]):
        return "high"
    if any(w in lower for w in ["moderate", "medium", "within 24", "within 48", "recommend seeing", "doctor visit"]):
        return "medium"
    if any(w in lower for w in ["low severity", "self-care", "mild", "rest and hydration", "हल्का"]):
        return "low"
    return None


def run_triage_agent(
    messages: list[dict],
    patient_name: str,
    patient_id: Optional[int] = None,
    language: str = "en",
    max_tool_rounds: int = 6,
) -> dict:
    """
    Run a multi-turn tool-calling triage agent.

    Returns:
        {
            "response_message": str,
            "severity": str | None,
            "action": "NONE" | "SHOW_SLOTS" | "REDIRECT_TO_CONFIRMATION",
            "available_slots": list[dict],  # populated when action is SHOW_SLOTS
            "booking_details": optional dict,
        }
    """
    user_text = _latest_user_text(messages)
    context_chunks = get_relevant_context(user_text, k=3) if user_text else []
    formatted_context = (
        "\n---\n".join(context_chunks) if context_chunks else "No specific guidelines found."
    )

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        patient_name=patient_name or "Patient",
        language=language or "en",
        context=formatted_context,
    )

    llm = ChatOllama(model=settings.OLLAMA_MODEL, temperature=0)
    llm_with_tools = llm.bind_tools(TOOLS)

    lc_messages = _to_langchain_messages(system_prompt, messages)
    booking_details: Optional[dict] = None
    available_slots: list[dict] = []
    severity: Optional[str] = None

    try:
        for _ in range(max_tool_rounds):
            ai_msg: AIMessage = llm_with_tools.invoke(lc_messages)
            lc_messages.append(ai_msg)

            tool_calls = getattr(ai_msg, "tool_calls", None) or []
            if not tool_calls:
                break

            for call in tool_calls:
                name = call.get("name")
                args = call.get("args") or {}
                call_id = call.get("id") or name

                tool_fn = TOOL_MAP.get(name)
                if tool_fn is None:
                    result_str = json.dumps({"error": f"Unknown tool: {name}"})
                else:
                    try:
                        result_str = tool_fn.invoke(args)
                    except Exception as tool_err:
                        result_str = json.dumps({"error": str(tool_err)})

                # Capture structured slot data for the API response
                if name == "check_available_slots":
                    try:
                        parsed = json.loads(result_str) if isinstance(result_str, str) else result_str
                        if isinstance(parsed, dict) and parsed.get("found") and parsed.get("slots"):
                            available_slots = parsed["slots"]
                    except (json.JSONDecodeError, TypeError):
                        pass

                # Capture successful booking for the API response envelope
                if name == "book_appointment":
                    try:
                        parsed = json.loads(result_str) if isinstance(result_str, str) else result_str
                        if isinstance(parsed, dict) and parsed.get("success"):
                            booking_details = {
                                "appointment_id": parsed.get("appointment_id"),
                                "doctor_name": parsed.get("doctor_name", ""),
                                "specialty": parsed.get("specialty", ""),
                                "clinic_name": parsed.get("clinic_name", ""),
                                "date": parsed.get("date", ""),
                                "time_slot": parsed.get("time_slot", ""),
                                "fee": parsed.get("fee", 0.0),
                            }
                            # Set patient_id on the appointment if available
                            if patient_id and parsed.get("appointment_id"):
                                _set_patient_on_appointment(
                                    appointment_id=parsed["appointment_id"],
                                    patient_id=patient_id,
                                )
                    except (json.JSONDecodeError, TypeError):
                        pass

                lc_messages.append(
                    ToolMessage(content=str(result_str), tool_call_id=call_id)
                )

        # Extract the last AI message with textual content
        response_message = ""
        for msg in reversed(lc_messages):
            if isinstance(msg, AIMessage) and not (getattr(msg, "tool_calls", None) or []):
                response_message = _extract_text(msg.content)
                if response_message:
                    break

        if not response_message:
            response_message = (
                "I'm here to help with your symptoms and scheduling. "
                "Could you please tell me more about how you're feeling?"
            )

        # Handle models that return JSON blobs instead of natural text
        parsed_blob = _try_parse_json_blob(response_message)
        if parsed_blob:
            response_message = str(
                parsed_blob.get("response_message")
                or parsed_blob.get("message")
                or response_message
            )
            if parsed_blob.get("booking_details") and not booking_details:
                bd = parsed_blob["booking_details"]
                if isinstance(bd, dict):
                    booking_details = {
                        "appointment_id": bd.get("appointment_id") or bd.get("id"),
                        "doctor_name": bd.get("doctor_name", ""),
                        "specialty": bd.get("specialty", ""),
                        "clinic_name": bd.get("clinic_name", bd.get("clinic", "")),
                        "date": bd.get("date", ""),
                        "time_slot": bd.get("time_slot", bd.get("time", "")),
                        "fee": bd.get("fee", 0.0),
                    }

        # Detect severity from response
        severity = _detect_severity(response_message)

    except Exception as e:
        print(f"[Agent] Triage agent fallback triggered: {e}")
        response_message = _fallback_message(user_text, language)
        severity = _detect_severity_from_input(user_text)

    # Determine action
    if booking_details:
        action = "REDIRECT_TO_CONFIRMATION"
    elif available_slots:
        action = "SHOW_SLOTS"
    else:
        action = "NONE"

    return {
        "response_message": response_message,
        "severity": severity,
        "action": action,
        "available_slots": available_slots,
        "booking_details": booking_details,
    }


def _set_patient_on_appointment(appointment_id: int, patient_id: int) -> None:
    """Set patient_id on an appointment that was created by the tool (without patient context)."""
    db = SessionLocal()
    try:
        appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if appt and not appt.patient_id:
            appt.patient_id = patient_id
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"[Agent] Failed to set patient on appointment: {e}")
    finally:
        db.close()


def _detect_severity_from_input(user_text: str) -> Optional[str]:
    """Heuristic severity from user symptom text."""
    lower = (user_text or "").lower()
    if any(t in lower for t in ["thunderclap", "chest pain", "breathing issue", "unconscious", "stroke"]):
        return "emergency"
    if any(t in lower for t in ["severe", "unbearable", "extreme", "can't breathe"]):
        return "high"
    if any(t in lower for t in ["fever", "cough", "headache", "vomiting", "pain"]):
        return "medium"
    return "low"


def _fallback_message(user_text: str, language: str) -> str:
    """Fallback response when the LLM agent fails."""
    lower = (user_text or "").lower()
    if any(t in lower for t in ["thunderclap", "chest pain", "breathing issue", "unconscious", "stroke"]):
        return (
            "Your symptoms may require emergency care. Please call emergency services "
            "or go to the nearest emergency room immediately."
        )
    if any(t in lower for t in ["fever", "cough", "headache", "vomiting", "pain"]):
        return (
            "Based on what you've shared, I recommend seeing a doctor within 24–48 hours. "
            "What day works best for an appointment?"
        )
    return (
        "Thank you for sharing. Could you describe your symptoms in a bit more detail "
        "so I can help guide you?"
    )
