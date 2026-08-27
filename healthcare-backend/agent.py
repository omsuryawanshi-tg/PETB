"""
Multi-turn conversational triage agent with tool calling via local Qwen 2.5 (Ollama).
"""
import json
import re
from datetime import datetime
from typing import Any, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

from database import SessionLocal
import models
from rag_service import get_relevant_context

# Friendly display names for seeded doctor IDs
DOCTOR_NAMES = {
    "DOC-101": "Dr. Smith",
    "DOC-102": "Dr. Johnson",
    "DOC-103": "Dr. Williams",
    "DOC-104": "Dr. Patel",
    "DOC-105": "Dr. Chen",
}

SYSTEM_PROMPT_TEMPLATE = """You are an empathetic AI medical triage nurse helping patients assess symptoms and book appointments when needed.

PATIENT NAME: {patient_name}
RESPONSE LANGUAGE: {language}

CLINICAL REFERENCE GUIDELINES (use these to assess severity):
{context}

YOUR WORKFLOW:
1. Listen carefully to the patient's symptoms. Be warm, calm, and clear.
2. Assess severity using the clinical guidelines (Low / Moderate / High / Emergency).
3. If symptoms are Low severity: give self-care advice. Do NOT push booking unless the patient asks.
4. If symptoms are Moderate, High, or Emergency-adjacent (but not immediate 911): recommend seeing a doctor and ask for their preferred day or date for an appointment.
5. When the patient specifies a day or date, call the check_slots tool to find available appointments.
6. Present available slots clearly (include slot ID, doctor name, date, and time) and ask which one they want.
7. When the patient selects a slot, call book_appointment_slot with that slot_id and the patient name "{patient_name}".
8. After a successful booking, confirm the appointment warmly and mention they will be redirected for confirmation.

EMERGENCY RULE:
If symptoms suggest a true emergency (e.g. thunderclap headache, chest pain with shortness of breath, stroke signs, unconsciousness), urge them to call emergency services / go to the ER immediately. Do not book a routine appointment in that case.

TOOL RULES:
- Call check_slots only when the user has indicated a preferred day or date.
- Call book_appointment_slot only when the user has clearly chosen a specific slot (by ID or by uniquely identifying time/doctor).
- Always pass patient_name="{patient_name}" when booking.
- Never invent slots — only use tool results.

After tools finish (or if no tools are needed), reply to the patient in natural language in {language}. Do not wrap your reply in JSON or markdown code fences.
"""


def _doctor_display_name(doctor_id: str) -> str:
    return DOCTOR_NAMES.get(doctor_id, doctor_id)


def _slot_matches_day(day_or_date: str, slot_date: str) -> bool:
    """Flexible match of user day/date text against a YYYY-MM-DD slot date."""
    query = day_or_date.strip().lower()
    if not query:
        return False

    if query in slot_date.lower():
        return True

    try:
        dt = datetime.strptime(slot_date, "%Y-%m-%d")
    except ValueError:
        return query in slot_date.lower()

    day_name = dt.strftime("%A").lower()
    day_abbr = dt.strftime("%a").lower()
    if query in (day_name, day_abbr) or day_name.startswith(query) or query.startswith(day_name):
        return True

    # e.g. "august 15", "aug 15", "15 august"
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


@tool
def check_slots(day_or_date: str) -> str:
    """Query SQLite for available appointment slots matching a day name or date.
    Use when the patient specifies a preferred day or date (e.g. 'Friday', '2026-08-15', 'August 16').
    Returns available slots with IDs, doctor names, dates, and times.
    """
    db = SessionLocal()
    try:
        available = (
            db.query(models.Appointment)
            .filter(models.Appointment.status == "available")
            .all()
        )
        matched = [s for s in available if _slot_matches_day(day_or_date, s.date)]

        if not matched:
            all_dates = sorted({s.date for s in available})
            return json.dumps({
                "found": False,
                "message": f"No available slots found for '{day_or_date}'.",
                "hint": f"Available dates currently in the system: {all_dates}" if all_dates else "No available slots in the system.",
            })

        slots = [
            {
                "slot_id": s.id,
                "doctor_id": s.doctor_id,
                "doctor_name": _doctor_display_name(s.doctor_id),
                "date": s.date,
                "time_slot": s.time_slot,
                "status": s.status,
            }
            for s in matched
        ]
        return json.dumps({"found": True, "count": len(slots), "slots": slots})
    except Exception as e:
        return json.dumps({"found": False, "error": str(e)})
    finally:
        db.close()


@tool
def book_appointment_slot(slot_id: int, patient_name: str) -> str:
    """Book an available appointment slot by ID for the given patient.
    Use when the patient has selected a specific slot. Updates status to 'booked' and returns confirmation details.
    """
    db = SessionLocal()
    try:
        slot = (
            db.query(models.Appointment)
            .filter(models.Appointment.id == slot_id)
            .first()
        )
        if not slot:
            return json.dumps({
                "success": False,
                "error": f"Appointment slot ID {slot_id} was not found.",
            })
        if slot.status != "available":
            return json.dumps({
                "success": False,
                "error": f"Appointment slot ID {slot_id} is already booked.",
            })

        slot.status = "booked"
        slot.patient_name = patient_name
        db.commit()
        db.refresh(slot)

        confirmation = {
            "success": True,
            "confirmation_id": str(slot.id),
            "appointment_id": slot.id,
            "doctor_id": slot.doctor_id,
            "doctor_name": _doctor_display_name(slot.doctor_id),
            "date": slot.date,
            "time_slot": slot.time_slot,
            "patient_name": slot.patient_name,
            "status": slot.status,
        }
        return json.dumps(confirmation)
    except Exception as e:
        db.rollback()
        return json.dumps({"success": False, "error": str(e)})
    finally:
        db.close()


TOOLS = [check_slots, book_appointment_slot]
TOOL_MAP = {t.name: t for t in TOOLS}


def _latest_user_text(messages: list[dict]) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "user" and msg.get("content"):
            return str(msg["content"])
    return ""


def _to_langchain_messages(
    system_prompt: str,
    messages: list[dict],
) -> list:
    lc_messages: list = [SystemMessage(content=system_prompt)]
    for msg in messages:
        role = (msg.get("role") or "").lower()
        content = str(msg.get("content") or "")
        if role == "user":
            lc_messages.append(HumanMessage(content=content))
        elif role in ("assistant", "ai"):
            lc_messages.append(AIMessage(content=content))
        elif role == "system":
            # Extra system notes from client are appended as context, not replacing ours
            lc_messages.append(SystemMessage(content=content))
    return lc_messages


def _extract_text(content: Any) -> str:
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


def run_triage_agent(
    messages: list[dict],
    patient_name: str,
    language: str = "en",
    model: str = "qwen2.5:3b",
    max_tool_rounds: int = 6,
) -> dict:
    """
    Run a multi-turn tool-calling triage agent.

    Returns:
        {
            "response_message": str,
            "action": "NONE" | "REDIRECT_TO_CONFIRMATION",
            "booking_details": optional dict with appointment_id, doctor_id, date, time_slot
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

    llm = ChatOllama(model=model, temperature=0)
    llm_with_tools = llm.bind_tools(TOOLS)

    lc_messages = _to_langchain_messages(system_prompt, messages)
    booking_details: Optional[dict] = None

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

                # Ensure booking always uses the known patient name when provided
                if name == "book_appointment_slot" and patient_name:
                    args = {**args, "patient_name": patient_name}

                tool_fn = TOOL_MAP.get(name)
                if tool_fn is None:
                    result_str = json.dumps({"error": f"Unknown tool: {name}"})
                else:
                    try:
                        result_str = tool_fn.invoke(args)
                    except Exception as tool_err:
                        result_str = json.dumps({"error": str(tool_err)})

                # Capture successful booking for the API response envelope
                if name == "book_appointment_slot":
                    try:
                        parsed = json.loads(result_str) if isinstance(result_str, str) else result_str
                        if isinstance(parsed, dict) and parsed.get("success"):
                            booking_details = {
                                "appointment_id": parsed.get("appointment_id"),
                                "doctor_id": parsed.get("doctor_id"),
                                "date": parsed.get("date"),
                                "time_slot": parsed.get("time_slot"),
                            }
                    except (json.JSONDecodeError, TypeError):
                        pass

                lc_messages.append(
                    ToolMessage(content=str(result_str), tool_call_id=call_id)
                )

        # Prefer the last AI message that has textual content (no pending tools)
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

        # If the model unexpectedly returned JSON, lift response_message / action from it
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
                        "appointment_id": bd.get("appointment_id"),
                        "doctor_id": bd.get("doctor_id"),
                        "date": bd.get("date"),
                        "time_slot": bd.get("time_slot"),
                    }

    except Exception as e:
        print(f"[Warning] Triage agent fallback triggered: {e}")
        response_message = _fallback_message(user_text, language)

    action = "REDIRECT_TO_CONFIRMATION" if booking_details else "NONE"
    return {
        "response_message": response_message,
        "action": action,
        "booking_details": booking_details,
    }


def _fallback_message(user_text: str, language: str) -> str:
    lower = (user_text or "").lower()
    if any(
        term in lower
        for term in ["thunderclap", "chest pain", "breathing issue", "unconscious", "stroke"]
    ):
        return (
            "Your symptoms may require emergency care. Please call emergency services "
            "or go to the nearest emergency room immediately."
        )
    if any(term in lower for term in ["fever", "cough", "headache", "vomiting", "pain"]):
        return (
            "Based on what you've shared, I recommend seeing a doctor within 24–48 hours. "
            "What day works best for an appointment?"
        )
    return (
        "Thank you for sharing. Could you describe your symptoms in a bit more detail "
        "so I can help guide you?"
    )
