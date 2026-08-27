# 🗄️ SQLite & SQLAlchemy Database Guide

Welcome! This guide explains what SQLite and SQLAlchemy are, how the database setup was built for your Healthcare Triage backend, its current status, and how to test it like a real backend engineer.

---

## 💡 1. What Are SQLite & SQLAlchemy? (Explained Simply)

- **SQLite (`triage.db`)**: A lightweight, file-based relational database that stores data directly inside a single file on your disk (`triage.db`). It doesn't require installing complex database servers like PostgreSQL or MySQL.
- **SQLAlchemy (ORM)**: **Object-Relational Mapping (ORM)** library for Python. Instead of writing raw SQL commands (`CREATE TABLE`, `INSERT INTO`), SQLAlchemy lets you define database tables using Python classes (`Appointment`) and manipulate rows using Python code.

---

## 🏗️ 2. What Was Built in Your Project

We created 3 core backend files:

```
                  ┌──────────────────────┐
                  │     database.py      │ ──> (Creates SQLite Engine & SessionLocal)
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │      models.py       │ ──> (Defines Appointment table schema)
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │       main.py        │ ──> (Generates triage.db & provides get_db())
                  └──────────────────────┘
```

### Components Created:

1. **[database.py](file:///C:/projects/PETB/healthcare-backend/database.py)**:
   - Configures SQLite database file `sqlite:///./triage.db`.
   - Creates `SessionLocal` to handle database connections.
   - Sets up `Base` class for database models.

2. **[models.py](file:///C:/projects/PETB/healthcare-backend/models.py)**:
   - Defines the `Appointment` model mapped to table `appointments`:
     - `id`: Integer Primary Key (Auto-incrementing ID)
     - `patient_name`: Patient's name
     - `date`: Appointment date (e.g., "2026-08-15")
     - `time_slot`: Time (e.g., "10:00 AM")
     - `doctor_id`: Healthcare provider identifier
     - `status`: Slot status (default: `"available"`)

3. **[main.py Integration](file:///C:/projects/PETB/healthcare-backend/main.py)**:
   - `models.Base.metadata.create_all(bind=engine)`: Automatically creates `triage.db` and the `appointments` table when the server starts.
   - `get_db()`: FastAPI dependency that opens a database session for incoming API requests and closes it safely in a `finally` block.

---

## 🚦 3. Current Project Status: Is It Ready?

- ✅ **Database & Schema**: `100% Ready`. `triage.db` exists with the `appointments` table generated.
- ✅ **FastAPI Dependency**: `get_db()` function is defined and ready to inject database sessions into appointment endpoints (`GET /api/appointments/slots`, `POST /api/appointments/book`).

---

## 🧪 4. How to Test This Like a Real Backend Engineer

Here are 3 ways backend engineers inspect and test SQLite databases:

### Method 1: Python REPL Database Inspection (Fastest)

Launch Python in your terminal:

```bash
python
```

Run these commands to insert a dummy appointment row and query it back:

```python
from database import SessionLocal
from models import Appointment

# 1. Open DB session
db = SessionLocal()

# 2. Insert a test appointment
new_slot = Appointment(
    patient_name="John Doe",
    date="2026-08-20",
    time_slot="10:00 AM",
    doctor_id="DOC-101",
    status="booked"
)
db.add(new_slot)
db.commit()
db.refresh(new_slot)
print(f"Created Appointment ID: {new_slot.id}")

# 3. Query all appointments
appointments = db.query(Appointment).all()
for appt in appointments:
    print(f"ID: {appt.id} | Patient: {appt.patient_name} | Date: {appt.date} | Status: {appt.status}")

db.close()
```

---

### Method 2: Inspect via SQLite Command-Line Tool

In terminal, run `sqlite3` to view tables directly:

```bash
sqlite3 triage.db
```

Inside the SQLite prompt:

```sql
.tables
-- Output should display: appointments

.schema appointments
-- Displays the SQL CREATE TABLE structure

SELECT * FROM appointments;
-- Displays all rows stored in the database

.exit
```

---

### Method 3: Visual Inspection using DB Browser for SQLite / VSCode Extensions

- Install **DB Browser for SQLite** (free GUI application) or the **SQLite Viewer** extension in VS Code.
- Open [triage.db](file:///C:/projects/PETB/healthcare-backend/triage.db) directly to view, edit, and filter rows in a visual spreadsheet-like grid.

---

## 🎯 Summary Checklist

| Component | Status | Verification Method |
| :--- | :--- | :--- |
| **Database File (`triage.db`)** | ✅ Created | Check root folder for `triage.db` |
| **Table Schema (`appointments`)** | ✅ Generated | Run `python -c "import main"` |
| **ORM Models (`models.py`)** | ✅ Active | Check [models.py](file:///C:/projects/PETB/healthcare-backend/models.py) |
| **Session Dependency (`get_db`)** | ✅ Active | Check [main.py](file:///C:/projects/PETB/healthcare-backend/main.py) |
