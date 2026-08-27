from sqlalchemy import Column, Integer, String
from database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_name = Column(String, nullable=True)
    date = Column(String, nullable=False)
    time_slot = Column(String, nullable=False)
    doctor_id = Column(String, nullable=False)
    status = Column(String, default="available")
