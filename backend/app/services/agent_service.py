"""
Multi-turn conversational triage agent with tool calling via local Ollama LLM.
Enhanced to work with normalized DB schema (Doctor + AppointmentSlot + Appointment).
"""
import json
import re
from datetime import datetime
from typing import Any, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.appointment import Appointment, AppointmentSlot
from app.models.doctor import Doctor
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
6. Present available slots clearly (include slot ID, doctor name, specialty, date, time, clinic) and ask which one they want.
7. When the patient selects a slot, call book_appointment with that slot_id.
8. After a successful booking, confirm the appointment warmly and mention they will be redirected for confirmation.

EMERGENCY RULE:
If symptoms suggest a true emergency (thunderclap headache, chest pain with shortness of breath, stroke signs, unconsciousness), urge them to call emergency services / go to the ER immediately. Do not book a routine appointment.

TOOL RULES:
- Call check_available_slots only when the user has indicated a preferred day or date.
- Call book_appointment only when the user has clearly chosen a specific slot (by ID or uniquely identifying time/doctor).
- Never invent slots — only use tool results.

SEVERITY ASSESSMENT:
After each response, mentally note the severity level. Include severity assessment in your thinking but respond naturally to the patient.

After tools finish (or if no tools are needed), reply to the patient in natural language in {language}. Do not wrap your reply in JSON or markdown code fences.
"""


def _slot_matches_day(day_or_date: str, slot_date: str) -> bool:
    """Flexible match of user day/date text against a YYYY-MM-DD slot date."""
    query = day_or_date.strip().lower()
    if not query:
        return False

    # Direct substring match (e.g. "2026-08-29")
    if query in slot_date.lower():
        return True

    # Handle "today", "tomorrow"
    today = datetime.now().date()
    if query in ("today", "aaj", "आज"):
        return slot_date == today.strftime("%Y-%m-%d")
    if query in ("tomorrow", "kal", "कल"):
        from datetime import timedelta
        return slot_date == (today + timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        dt = datetime.strptime(slot_date, "%Y-%m-%d")
    except ValueError:
        return query in slot_date.lower()

    day_name = dt.strftime("%A").lower()
    day_abbr = dt.strftime("%a").lower()
    if query in (day_name, day_abbr) or day_name.startswith(query) or query.startswith(day_name):
        return True

    formats = [
        dt.strftime("%B %d").lower(),
        dt.strftime("%b %d").lower(),
        dt.strftime("%d %B").lower(),
        dt.strftime("%d %b").lower(),
        dt.strftime("%B %d, %Y").lower(),
        dt.strftime("%m/%d").lower(),
        dt.strftime("%m/%d/%Y").lower(),
    ]
    return any(query in fmt or fmt in query for fmt in formats)


def _format_time_12h(time_24h: str) -> str:
    """Convert HH:MM 24h to 12h format (e.g. '09:00' → '9:00 AM')."""
    try:
        dt = datetime.strptime(time_24h, "%H:%M")
        return dt.strftime("%-I:%M %p") if hasattr(dt, 'strftime') else dt.strftime("%I:%M %p").lstrip("0")
    except (ValueError, AttributeError):
        try:
            dt = datetime.strptime(time_24h, "%H:%M")
            result = dt.strftime("%I:%M %p")
            return result.lstrip("0") if result.startswith("0") else result
        except ValueError:
            return time_24h


@tool
def check_available_slots(day_or_date: str) -> str:
    """Query the database for available appointment slots matching a day name or date.
    Use when the patient specifies a preferred day or date (e.g. 'Friday', '2026-08-29', 'tomorrow').
    Returns available slots with IDs, doctor names, specialties, dates, times, and clinics.
    """
    db = SessionLocal()
    try:
        available = (
            db.query(AppointmentSlot, Doctor)
            .join(Doctor, AppointmentSlot.doctor_id == Doctor.id)
            .filter(AppointmentSlot.status == "available")
            .all()
        )
        matched = [
            (slot, doc) for slot, doc in available
            if _slot_matches_day(day_or_date, slot.date)
        ]

        if not matched:
            all_dates = sorted({s.date for s, _ in available})
            return json.dumps({
                "found": False,
                "message": f"No available slots found for '{day_or_date}'.",
                "available_dates": all_dates if all_dates else [],
                "hint": f"Available dates: {', '.join(all_dates)}" if all_dates else "No available slots in the system.",
            })

        slots = [
            {
                "slot_id": slot.id,
                "doctor_name": doc.name,
                "specialty": doc.specialty,
                "clinic": doc.clinic_name,
                "consultation_fee": doc.consultation_fee,
                "rating": doc.rating,
                "date": slot.date,
                "time": _format_time_12h(slot.start_time),
                "end_time": _format_time_12h(slot.end_time),
            }
            for slot, doc in matched
        ]
        return json.dumps({"found": True, "count": len(slots), "slots": slots})
    except Exception as e:
        return json.dumps({"found": False, "error": str(e)})
    finally:
        db.close()


@tool
def book_appointment(slot_id: int) -> str:
    """Book an available appointment slot by slot ID for the current patient.
    Use when the patient has selected a specific slot. Updates slot status to 'booked' and creates an appointment record.
    """
    db = SessionLocal()
    try:
        slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == slot_id).first()
        if not slot:
            return json.dumps({"success": False, "error": f"Slot #{slot_id} not found."})
        if slot.status != "available":
            return json.dumps({"success": False, "error": f"Slot #{slot_id} is already booked."})

        doctor = db.query(Doctor).filter(Doctor.id == slot.doctor_id).first()

        # Mark slot as booked
        slot.status = "booked"
        db.commit()
        db.refresh(slot)

        confirmation = {
            "success": True,
            "slot_id": slot.id,
            "doctor_name": doctor.name if doctor else "Doctor",
            "specialty": doctor.specialty if doctor else "",
            "clinic": doctor.clinic_name if doctor else "",
            "date": slot.date,
            "time": _format_time_12h(slot.start_time),
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
            "action": "NONE" | "REDIRECT_TO_CONFIRMATION",
            "booking_details": optional dict
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

                # Capture successful booking for the API response envelope
                if name == "book_appointment":
                    try:
                        parsed = json.loads(result_str) if isinstance(result_str, str) else result_str
                        if isinstance(parsed, dict) and parsed.get("success"):
                            booking_details = {
                                "appointment_id": parsed.get("slot_id"),
                                "doctor_name": parsed.get("doctor_name", ""),
                                "specialty": parsed.get("specialty", ""),
                                "date": parsed.get("date", ""),
                                "time": parsed.get("time", ""),
                                "clinic": parsed.get("clinic", ""),
                            }
                            # Create actual Appointment record if patient_id is available
                            if patient_id:
                                _create_appointment_record(
                                    patient_id=patient_id,
                                    slot_id=parsed.get("slot_id"),
                                    booking_details=booking_details,
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
                        "appointment_id": bd.get("appointment_id") or bd.get("slot_id"),
                        "doctor_name": bd.get("doctor_name", ""),
                        "specialty": bd.get("specialty", ""),
                        "date": bd.get("date", ""),
                        "time": bd.get("time", bd.get("time_slot", "")),
                        "clinic": bd.get("clinic", ""),
                    }

        # Detect severity from response
        severity = _detect_severity(response_message)

    except Exception as e:
        print(f"[Agent] Triage agent fallback triggered: {e}")
        response_message = _fallback_message(user_text, language)
        severity = _detect_severity_from_input(user_text)

    action = "REDIRECT_TO_CONFIRMATION" if booking_details else "NONE"
    return {
        "response_message": response_message,
        "severity": severity,
        "action": action,
        "booking_details": booking_details,
    }


def _create_appointment_record(patient_id: int, slot_id: int, booking_details: dict) -> None:
    """Create an Appointment record in the database after successful tool booking."""
    db = SessionLocal()
    try:
        existing = db.query(Appointment).filter(Appointment.slot_id == slot_id).first()
        if existing:
            return  # Already booked

        appt = Appointment(
            patient_id=patient_id,
            slot_id=slot_id,
            booking_status="confirmed",
        )
        db.add(appt)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[Agent] Failed to create appointment record: {e}")
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
