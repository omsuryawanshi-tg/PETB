"""
Triage Session ORM model — records of AI triage conversations.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class TriageSession(Base):
    __tablename__ = "triage_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    chief_complaint = Column(Text, nullable=True)
    severity = Column(String(20), nullable=True)  # low | medium | high | emergency
    ai_recommendation = Column(Text, nullable=True)
    raw_conversation_history = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    patient = relationship("User", back_populates="triage_sessions")
    appointment = relationship("Appointment", back_populates="triage_session", uselist=False)

    def __repr__(self) -> str:
        return f"<TriageSession id={self.id} patient_id={self.patient_id} severity={self.severity!r}>"
