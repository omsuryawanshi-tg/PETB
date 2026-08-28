"""
User ORM model — patients and admin accounts.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    role = Column(String(20), nullable=False, default="patient")  # "patient" | "admin"
    preferred_language = Column(String(5), nullable=False, default="en")  # "en" | "hi"
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    appointments = relationship("Appointment", back_populates="patient", lazy="dynamic")
    triage_sessions = relationship("TriageSession", back_populates="patient", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"
