import uvicorn
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import SessionLocal, engine
import models
from agent import run_triage_agent

# Generate database tables automatically on application startup
models.Base.metadata.create_all(bind=engine)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_dummy_appointments():
    """Populates database with 5 dummy 'available' appointment slots if table is empty."""
    db = SessionLocal()
    try:
        count = db.query(models.Appointment).count()
        if count == 0:
            dummy_slots = [
                models.Appointment(patient_name=None, date="2026-08-15", time_slot="09:00 AM", doctor_id="DOC-101", status="available"),
                models.Appointment(patient_name=None, date="2026-08-15", time_slot="11:30 AM", doctor_id="DOC-101", status="available"),
                models.Appointment(patient_name=None, date="2026-08-15", time_slot="02:00 PM", doctor_id="DOC-102", status="available"),
                models.Appointment(patient_name=None, date="2026-08-16", time_slot="10:00 AM", doctor_id="DOC-103", status="available"),
                models.Appointment(patient_name=None, date="2026-08-16", time_slot="03:30 PM", doctor_id="DOC-103", status="available"),
            ]
            db.add_all(dummy_slots)
            db.commit()
            print("[Database] Successfully populated database with 5 dummy available appointment slots.")
    except Exception as e:
        print(f"[Warning] Error during database seeding: {e}")
    finally:
        db.close()


app = FastAPI(
    title="Healthcare Triage Bot API",
    description="Backend API for AI-powered Healthcare Triage and Appointment Scheduling with Local RAG & Ollama LLM",
    version="1.1.0",
)


@app.on_event("startup")
def on_startup():
    seed_dummy_appointments()


# CORS Configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Schemas
class ChatRequest(BaseModel):
    messages: List[dict] = Field(
        ...,
        description="Multi-turn conversation history. Each item has 'role' and 'content'.",
        examples=[[{"role": "user", "content": "I have a fever and headache"}]],
    )
    patient_name: str = Field(..., description="Full name of the patient")
    language: str = Field(default="en", description="Language code for the response (e.g. 'en', 'es')")


class BookingDetails(BaseModel):
    appointment_id: int = Field(..., description="Booked appointment slot ID")
    doctor_id: str = Field(..., description="Doctor or provider identifier")
    date: str = Field(..., description="Appointment date (YYYY-MM-DD)")
    time_slot: str = Field(..., description="Appointment time slot")


class ChatResponse(BaseModel):
    response_message: str = Field(..., description="Assistant reply for the patient")
    action: str = Field(
        default="NONE",
        description="NONE or REDIRECT_TO_CONFIRMATION after a successful booking",
    )
    booking_details: Optional[BookingDetails] = Field(
        default=None,
        description="Present when action is REDIRECT_TO_CONFIRMATION",
    )


class AppointmentSlot(BaseModel):
    id: int = Field(..., description="Unique ID for the slot")
    patient_name: Optional[str] = Field(default=None, description="Name of patient if booked")
    date: str = Field(..., description="Date of the slot (YYYY-MM-DD)")
    time_slot: str = Field(..., description="Time slot (e.g., 10:00 AM)")
    doctor_id: str = Field(..., description="Doctor or provider identifier")
    status: str = Field(default="available", description="Availability status ('available' or 'booked')")

    class Config:
        from_attributes = True


class BookingRequest(BaseModel):
    appointment_id: int = Field(..., description="ID of the appointment slot to book")
    patient_name: str = Field(..., description="Full name of the patient")
    patient_email: Optional[str] = Field(default=None, description="Email address")
    patient_phone: Optional[str] = Field(default=None, description="Phone number")
    notes: Optional[str] = Field(default=None, description="Additional medical notes or reason for visit")


class BookingResponse(BaseModel):
    success: bool = Field(..., description="Whether booking succeeded")
    message: str = Field(..., description="Status message")
    booking_id: Optional[str] = Field(default=None, description="Confirmation booking reference ID")


# API Routes
@app.get("/")
def read_root():
    return {"status": "online", "message": "Healthcare Triage Bot API with Local RAG & Ollama is running"}


@app.post("/api/chat", response_model=ChatResponse)
def handle_chat(request: ChatRequest):
    """
    Multi-turn triage chatbot with tool calling.
    Accepts conversation history, runs Qwen 2.5 via Ollama with check_slots / book_appointment_slot tools,
    and returns response_message plus optional booking redirect details.
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages must contain at least one entry.")

    result = run_triage_agent(
        messages=request.messages,
        patient_name=request.patient_name,
        language=request.language,
    )

    booking = result.get("booking_details")
    return ChatResponse(
        response_message=result.get("response_message", ""),
        action=result.get("action", "NONE"),
        booking_details=BookingDetails(**booking) if booking else None,
    )


@app.get("/api/appointments/slots", response_model=List[AppointmentSlot])
def get_appointment_slots(db: Session = Depends(get_db)):
    """
    Retrieves all available doctor appointment slots from SQLite database.
    """
    slots = db.query(models.Appointment).filter(models.Appointment.status == "available").all()
    return slots


@app.post("/api/appointments/book", response_model=BookingResponse)
def book_appointment(booking: BookingRequest, db: Session = Depends(get_db)):
    """
    Books an appointment slot for a patient by appointment_id, updating status to 'booked' in SQLite database.
    """
    slot = db.query(models.Appointment).filter(models.Appointment.id == booking.appointment_id).first()

    if not slot:
        raise HTTPException(
            status_code=404,
            detail=f"Appointment slot ID {booking.appointment_id} not found."
        )

    if slot.status != "available":
        raise HTTPException(
            status_code=400,
            detail=f"Appointment slot ID {booking.appointment_id} is already booked."
        )

    # Update slot status to 'booked' and save patient name
    slot.status = "booked"
    slot.patient_name = booking.patient_name

    db.commit()
    db.refresh(slot)

    return BookingResponse(
        success=True,
        message=f"Appointment for '{booking.patient_name}' successfully booked for slot #{slot.id}.",
        booking_id=str(slot.id),
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
