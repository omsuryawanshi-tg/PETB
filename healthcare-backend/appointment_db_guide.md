# 📅 Database Appointment Workflow & Testing Guide

Welcome! This guide explains the complete appointment database workflow built into your Healthcare Triage backend, how data flows into SQLite (`triage.db`), how to test it step-by-step like a real backend engineer, and how to populate more appointment slots.

---

## 💡 1. What Was Built & How It Works (Explained Simply)

Previously, appointment slots were temporary fake data stored in Python memory. If the server restarted, any bookings were lost.

Now, your appointment slots are backed by a real **SQLite Database (`triage.db`)**!

### End-to-End Data Flow:

```
[ User / Frontend ]
        │
        │ 1. HTTP Request (GET /api/appointments/slots or POST /api/appointments/book)
        ▼
[ FastAPI App (main.py) ]
        │
        │ 2. get_db() opens a database session
        ▼
[ SQLAlchemy ORM (models.py) ]
        │
        │ 3. Executes SQL query (SELECT / UPDATE)
        ▼
[ SQLite File (triage.db) ]
        │
        │ 4. Commits changes & returns updated appointment data
        ▼
[ JSON Response to Client ]
```

---

## 🛠️ 2. Key Components Implemented

1. **Automatic Database Seeder (`seed_dummy_appointments()`)**:
   - Runs automatically on server startup (`@app.on_event("startup")`).
   - If `triage.db` is empty, it populates 5 initial available doctor slots automatically.

2. **`GET /api/appointments/slots`**:
   - Uses `db: Session = Depends(get_db)`.
   - Queries `triage.db` for all records where `status == "available"`.
   - Once a slot is booked, it disappears from this endpoint automatically!

3. **`POST /api/appointments/book`**:
   - Accepts `appointment_id` and `patient_name`.
   - Looks up the specific slot by ID in `triage.db`.
   - Changes `status` from `"available"` to `"booked"`, assigns `patient_name`, and executes `db.commit()`.

---

## 🧪 3. How to Test Like a Real Backend Engineer (Step-by-Step)

Follow these steps to observe how making an API request permanently updates the SQLite database file:

### Step 1: Start the Backend Server

Open your terminal in `C:\projects\PETB\healthcare-backend`:

```bash
uvicorn main:app --reload
```

In the terminal output, you will see:
`[Database] Successfully populated database with 5 dummy available appointment slots.`

---

### Step 2: Test via FastAPI Swagger UI (`http://127.0.0.1:8000/docs`)

1. Open **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** in your web browser.
2. **Fetch Available Slots**:
   - Expand `GET /api/appointments/slots` ➔ Click **Try it out** ➔ **Execute**.
   - Note the returned array of 5 available slots (`id: 1`, `id: 2`, etc.).
3. **Book an Appointment**:
   - Expand `POST /api/appointments/book` ➔ Click **Try it out**.
   - Enter request body:
     ```json
     {
       "appointment_id": 1,
       "patient_name": "Sarah Connor"
     }
     ```
   - Click **Execute**.
   - **Response**: `{"success": true, "message": "Appointment for 'Sarah Connor' successfully booked for slot #1.", "booking_id": "1"}`

4. **Verify Database Update**:
   - Execute `GET /api/appointments/slots` again.
   - **Notice**: Slot `#1` is no longer returned because its status in `triage.db` changed to `"booked"`!

---

### Step 3: Verify Directly Inside `triage.db` via Terminal

Run this command in terminal to query the SQLite database directly:

```bash
sqlite3 triage.db "SELECT id, patient_name, date, time_slot, status FROM appointments;"
```

**Output:**
```
1|Sarah Connor|2026-08-15|09:00 AM|booked
2||2026-08-15|11:30 AM|available
3||2026-08-15|02:00 PM|available
4||2026-08-16|10:00 AM|available
5||2026-08-16|03:30 PM|available
```
*Slot #1 permanently reflects `patient_name = Sarah Connor` and `status = booked`!*

---

## ➕ 4. How to Add More Appointment Slots

Currently, 5 slots are seeded. Here are 3 ways to add as many slots as you want:

### Option A: Modify the Seeder Function in `main.py` (Easiest)

Open [main.py](file:///C:/projects/PETB/healthcare-backend/main.py) and update `seed_dummy_appointments()` to add more slots:

```python
dummy_slots = [
    models.Appointment(patient_name=None, date="2026-08-15", time_slot="09:00 AM", doctor_id="DOC-101", status="available"),
    models.Appointment(patient_name=None, date="2026-08-15", time_slot="11:30 AM", doctor_id="DOC-101", status="available"),
    models.Appointment(patient_name=None, date="2026-08-15", time_slot="02:00 PM", doctor_id="DOC-102", status="available"),
    models.Appointment(patient_name=None, date="2026-08-16", time_slot="10:00 AM", doctor_id="DOC-103", status="available"),
    models.Appointment(patient_name=None, date="2026-08-16", time_slot="03:30 PM", doctor_id="DOC-103", status="available"),
    # Add new slots here:
    models.Appointment(patient_name=None, date="2026-08-17", time_slot="09:30 AM", doctor_id="DOC-104", status="available"),
    models.Appointment(patient_name=None, date="2026-08-17", time_slot="01:00 PM", doctor_id="DOC-104", status="available"),
    models.Appointment(patient_name=None, date="2026-08-18", time_slot="11:00 AM", doctor_id="DOC-105", status="available"),
]
```

---

### Option B: Add Slots via Python Terminal Script

Run this single python command in terminal anytime to add 10 new slots:

```bash
python -c "
from database import SessionLocal
import models

db = SessionLocal()
new_slots = [
    models.Appointment(date='2026-08-20', time_slot=f'{hour}:00 PM', doctor_id='DOC-201', status='available')
    for hour in range(1, 6)
]
db.add_all(new_slots)
db.commit()
print('Added 5 new slots!')
db.close()
"
```

---

### Option C: Reset / Clear Database to Re-seed

If you ever want to wipe the database and start fresh with empty slots:
1. Stop the server (`CTRL + C`).
2. Delete `triage.db`:
   ```bash
   rm triage.db
   ```
3. Restart `uvicorn main:app --reload`. The database and fresh slots will be recreated automatically!

---

## 🎯 Summary Table

| Operation | Endpoint / Command | Effect in `triage.db` |
| :--- | :--- | :--- |
| **Get Available Slots** | `GET /api/appointments/slots` | `SELECT * WHERE status = 'available'` |
| **Book Slot** | `POST /api/appointments/book` | `UPDATE appointments SET status='booked', patient_name='...' WHERE id=...` |
| **Direct DB Query** | `sqlite3 triage.db` | Inspects rows on disk |
