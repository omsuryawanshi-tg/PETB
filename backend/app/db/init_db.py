"""
Database seeder — populates doctors, appointment slots, and clinical guideline files.
Designed to be idempotent (only seeds if tables are empty).
"""
import os
from datetime import date, timedelta

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.appointment import AppointmentSlot
from app.models.doctor import Doctor
from app.models.user import User


# ─── Doctors Seed Data ───────────────────────────────────────────────────────

SEED_DOCTORS = [
    {
        "name": "Dr. Aditi Rao",
        "specialty": "General Medicine",
        "clinic_name": "CareConnect Central Clinic",
        "consultation_fee": 400.0,
        "rating": 4.6,
    },
    {
        "name": "Dr. Vikram Mehta",
        "specialty": "Pulmonology",
        "clinic_name": "BreathEasy Lung & Chest Centre",
        "consultation_fee": 700.0,
        "rating": 4.8,
    },
    {
        "name": "Dr. Sneha Kulkarni",
        "specialty": "Pediatrics",
        "clinic_name": "Little Stars Children's Hospital",
        "consultation_fee": 500.0,
        "rating": 4.7,
    },
    {
        "name": "Dr. Rajesh Sharma",
        "specialty": "Cardiology",
        "clinic_name": "HeartCare Advanced Cardiac Institute",
        "consultation_fee": 800.0,
        "rating": 4.9,
    },
    {
        "name": "Dr. Priya Nair",
        "specialty": "Dermatology",
        "clinic_name": "SkinGlow Dermatology & Wellness",
        "consultation_fee": 450.0,
        "rating": 4.5,
    },
]


# ─── Slot Time Templates ─────────────────────────────────────────────────────

SLOT_TIMES = [
    ("09:00", "09:30"),
    ("09:30", "10:00"),
    ("10:00", "10:30"),
    ("10:30", "11:00"),
    ("11:00", "11:30"),
    ("14:00", "14:30"),
    ("14:30", "15:00"),
    ("15:00", "15:30"),
    ("15:30", "16:00"),
    ("16:00", "16:30"),
]


# ─── Clinical Guidelines ─────────────────────────────────────────────────────

GUIDELINE_FILES = {
    "fever_guidelines.txt": """# Clinical Triage Guidelines: Fever & Febrile Illness Triage

## Overview
Fever is defined as a body temperature of 100.4°F (38.0°C) or higher. It is an immune response commonly caused by viral or bacterial infections.

## Red Flag Symptoms (Emergency - Immediate ER Evaluation)
- High fever exceeding 103°F (39.4°C) unresponsive to antipyretics.
- Fever accompanied by stiff neck, severe headache, confusion, or difficulty breathing.
- Non-blanching skin rash (petechiae or purpura).
- Infant under 3 months with temperature of 100.4°F (38.0°C) or higher.
- Signs of severe sepsis (extreme lethargy, rapid heart rate, low blood pressure, cold clammy extremities).

## Moderate Risk Symptoms (Urgent Physician Consultation within 24 Hours)
- Fever persisting for more than 3 consecutive days.
- Fever accompanied by localized pain (e.g., earache, severe sore throat, painful urination, productive cough with yellow/green sputum).
- Fever in immunocompromised patients (e.g., chemotherapy patients, elderly).

## Low Risk / Self-Care Guidelines
- Low-grade fever (100.4°F to 101.5°F) with mild cold symptoms, runny nose, or mild body aches.
- Recommendation: Adequate hydration, bed rest, and fever reducers (Acetaminophen 500mg every 6 hours or Ibuprofen 400mg every 8 hours for adults). Monitor temperature twice daily.
""",
    "headache_guidelines.txt": """# Clinical Triage Guidelines: Headache Assessment

## Overview
Headaches range from tension-type (most common) to potentially life-threatening conditions requiring immediate evaluation.

## Red Flag Symptoms (Emergency)
- Thunderclap headache: sudden, severe onset reaching maximum intensity within seconds.
- Headache with fever, stiff neck, and photophobia (meningitis triad).
- New headache with focal neurological deficits (weakness, vision loss, speech difficulty).
- Headache following head trauma with altered consciousness.
- Worst headache of life with nausea and vomiting.

## Moderate Risk (Physician Consultation within 24-48 Hours)
- New daily persistent headache lasting more than 3 days.
- Migraine with aura not previously evaluated.
- Headache worsening with position changes or Valsalva maneuver.
- Headache in patients over 50 with no prior history.

## Low Risk / Self-Care
- Tension-type headache: bilateral, pressing quality, mild-to-moderate.
- Recommendation: OTC analgesics (Acetaminophen 500mg or Ibuprofen 400mg), stress management, adequate sleep, hydration. Seek care if frequency exceeds 15 days/month.
""",
    "abdominal_pain_guidelines.txt": """# Clinical Triage Guidelines: Abdominal Pain Assessment

## Overview
Abdominal pain can range from benign (indigestion) to surgical emergencies (appendicitis, perforation).

## Red Flag Symptoms (Emergency)
- Severe, sudden-onset abdominal pain with rigid abdomen.
- Abdominal pain with bloody vomiting or black tarry stools.
- Pain with signs of shock (rapid pulse, low BP, pale skin, confusion).
- Suspected ectopic pregnancy (lower abdominal pain with missed period, vaginal bleeding).
- Pain with high fever (>102°F) and inability to keep fluids down.

## Moderate Risk (Urgent Consultation within 24 Hours)
- Persistent pain lasting more than 6 hours without improvement.
- Localized right lower quadrant pain (possible appendicitis).
- Pain with persistent vomiting or diarrhea causing dehydration signs.
- Abdominal pain with urinary symptoms (possible UTI or kidney stones).

## Low Risk / Self-Care
- Mild, intermittent cramping after meals, bloating, or gas.
- Recommendation: Small bland meals, adequate hydration, avoid spicy/fatty foods. Antacids for mild heartburn. Monitor for 24 hours and seek care if worsening.
""",
    "respiratory_guidelines.txt": """# Clinical Triage Guidelines: Respiratory Symptoms

## Overview
Respiratory symptoms include cough, shortness of breath, wheezing, and chest tightness. They may indicate infections, asthma, COPD, or cardiac conditions.

## Red Flag Symptoms (Emergency)
- Severe shortness of breath at rest or inability to speak in full sentences.
- Cyanosis (blue discoloration of lips or fingertips).
- Stridor (high-pitched breathing sound) indicating upper airway obstruction.
- Massive hemoptysis (coughing up large amounts of blood).
- Sudden chest pain with shortness of breath (possible pulmonary embolism).

## Moderate Risk (Physician Consultation within 24-48 Hours)
- Persistent cough lasting more than 3 weeks.
- Wheezing or chest tightness not responding to usual inhalers.
- Productive cough with discolored sputum and mild fever.
- Worsening of known asthma or COPD symptoms.

## Low Risk / Self-Care
- Common cold symptoms: mild cough, nasal congestion, sore throat.
- Recommendation: Rest, warm fluids, honey for cough relief (adults), saline nasal rinse. OTC decongestants if needed. Seek care if symptoms persist beyond 10 days.
""",
    "chest_pain_guidelines.txt": """# Clinical Triage Guidelines: Chest Pain Evaluation

## Overview
Chest pain requires careful evaluation as it may indicate cardiac emergencies or benign musculoskeletal conditions.

## Red Flag Symptoms (Emergency - Call 911)
- Crushing, pressure-like chest pain radiating to left arm, jaw, or back.
- Chest pain with shortness of breath, sweating, nausea, or lightheadedness.
- Known cardiac history with new or worsening chest pain.
- Chest pain with syncope (fainting) or near-syncope.
- Sharp, sudden chest pain with difficulty breathing (possible pneumothorax or PE).

## Moderate Risk (Same-Day Physician Evaluation)
- Chest pain reproducible with palpation but persistent.
- New chest pain with exertion that resolves with rest (possible stable angina).
- Chest pain with palpitations or irregular heartbeat.
- Pleuritic chest pain (sharp, worsens with breathing) with mild fever.

## Low Risk / Self-Care
- Brief, sharp chest pain related to movement or posture (musculoskeletal).
- Chest pain after heavy meal or with acid reflux symptoms.
- Recommendation: Rest, antacids for GERD symptoms, NSAIDs for musculoskeletal pain. Seek immediate care if pain worsens, recurs, or is accompanied by shortness of breath.
""",
    "skin_conditions_guidelines.txt": """# Clinical Triage Guidelines: Common Skin Conditions

## Overview
Skin complaints include rashes, lesions, itching, and infections. Most are non-urgent but some require prompt evaluation.

## Red Flag Symptoms (Emergency)
- Rapidly spreading rash with fever and systemic illness (possible meningococcemia, Stevens-Johnson syndrome).
- Skin infection with red streaking, high fever, and rapid progression (cellulitis/necrotizing fasciitis).
- Severe allergic reaction with hives AND difficulty breathing or throat swelling (anaphylaxis).
- Burns covering more than 10% body surface area or involving face/hands/genitals.

## Moderate Risk (Dermatology Consultation within 1-2 Weeks)
- New mole or changing mole (asymmetry, border irregularity, color variation, diameter >6mm).
- Persistent rash not responding to OTC treatment after 2 weeks.
- Recurrent skin infections (boils, abscesses).
- Widespread eczema flare affecting daily activities.

## Low Risk / Self-Care
- Mild contact dermatitis, insect bites, minor rashes.
- Recommendation: Topical hydrocortisone 1%, antihistamines for itching, moisturizers for dry skin. Avoid known allergens. Seek care if spreading or not improving in 7 days.
""",
    "musculoskeletal_guidelines.txt": """# Clinical Triage Guidelines: Musculoskeletal Pain

## Overview
Musculoskeletal complaints include joint pain, back pain, muscle strains, and injuries. Assessment focuses on ruling out fractures and serious conditions.

## Red Flag Symptoms (Emergency)
- Obvious deformity suggesting fracture or dislocation.
- Severe pain after trauma with inability to bear weight.
- Back pain with loss of bowel/bladder control (cauda equina syndrome).
- Joint pain with red, hot, swollen joint and fever (septic arthritis).
- Compartment syndrome signs: severe pain disproportionate to injury, tight swelling, pain with passive stretch.

## Moderate Risk (Physician Consultation within 48 Hours)
- Persistent joint swelling lasting more than 2 weeks.
- Back pain radiating down the leg with numbness or weakness.
- Sports injury with joint instability or locking.
- Worsening pain despite rest and OTC medications.

## Low Risk / Self-Care
- Mild muscle soreness after exercise, minor strains.
- Recommendation: RICE protocol (Rest, Ice, Compression, Elevation), OTC NSAIDs, gentle stretching after acute phase. Seek care if no improvement in 1 week.
""",
    "mental_health_guidelines.txt": """# Clinical Triage Guidelines: Mental Health Assessment

## Overview
Mental health symptoms include anxiety, depression, sleep disturbances, and acute psychiatric presentations.

## Red Flag Symptoms (Emergency)
- Active suicidal ideation with a plan or means.
- Homicidal thoughts or threats of violence.
- Acute psychosis (hallucinations, delusions, disorganized behavior).
- Severe agitation or catatonia.
- Overdose or self-harm requiring medical treatment.

## Moderate Risk (Mental Health Consultation within 1 Week)
- Persistent low mood, loss of interest, or hopelessness lasting more than 2 weeks.
- Panic attacks occurring frequently and affecting daily function.
- Significant sleep disturbance (insomnia or hypersomnia) affecting daily life.
- Increased substance use as coping mechanism.

## Low Risk / Self-Care
- Occasional stress, mild anxiety related to identifiable triggers.
- Recommendation: Regular exercise, sleep hygiene, mindfulness or relaxation techniques, social support. Consider counseling if symptoms persist. Crisis helpline numbers should always be provided.
""",
    "pediatric_guidelines.txt": """# Clinical Triage Guidelines: Pediatric Common Presentations

## Overview
Children require age-specific assessment. Key differences include faster deterioration, different vital sign ranges, and unique conditions.

## Red Flag Symptoms (Emergency)
- Infant under 3 months with fever ≥100.4°F (38°C).
- Child with difficulty breathing, nasal flaring, chest retractions, or grunting.
- Non-blanching rash (petechiae/purpura) in a child with fever.
- Inconsolable crying, bulging fontanelle, or extreme lethargy in infants.
- Severe dehydration: no tears, dry mouth, sunken eyes, no urine for 6+ hours.

## Moderate Risk (Pediatrician within 24 Hours)
- Fever lasting more than 3 days in children over 3 months.
- Persistent vomiting or diarrhea with mild dehydration signs.
- Ear pain with fever.
- Wheezing or persistent cough in a child with known asthma.
- Rash with mild fever but child otherwise active and feeding.

## Low Risk / Self-Care
- Common cold, mild cough, low-grade fever with child active and feeding well.
- Recommendation: Age-appropriate fever reducers (Acetaminophen or Ibuprofen for children over 6 months), encourage fluids, rest. Monitor closely and seek care if symptoms worsen or child becomes lethargic.
""",
    "diabetes_guidelines.txt": """# Clinical Triage Guidelines: Diabetes-Related Symptoms

## Overview
Diabetes-related presentations include hyperglycemia, hypoglycemia, and chronic complications requiring appropriate triage.

## Red Flag Symptoms (Emergency)
- Diabetic ketoacidosis (DKA): nausea, vomiting, fruity breath, rapid breathing, blood glucose >300 mg/dL with ketones.
- Severe hypoglycemia: confusion, seizures, loss of consciousness, blood glucose <54 mg/dL.
- Hyperosmolar hyperglycemic state: extreme thirst, very high blood glucose (>600 mg/dL), altered consciousness.
- Diabetic foot ulcer with signs of spreading infection (redness, warmth, drainage, fever).

## Moderate Risk (Physician Consultation within 24-48 Hours)
- Consistently elevated fasting blood glucose (>180 mg/dL) despite medication.
- Recurrent hypoglycemic episodes (more than 2 per week).
- New numbness or tingling in feet (peripheral neuropathy).
- Visual changes (blurring) in a diabetic patient.
- Non-healing wound on foot lasting more than 1 week.

## Low Risk / Self-Care
- Mild blood glucose fluctuations within expected range.
- Recommendation: Follow prescribed medication regimen, monitor blood glucose regularly, maintain balanced diet, regular exercise. Annual eye and foot examinations. Seek care if persistent readings outside target range.
""",
    "allergy_guidelines.txt": """# Clinical Triage Guidelines: Allergic Reactions

## Overview
Allergic reactions range from mild localized responses to life-threatening anaphylaxis requiring immediate treatment.

## Red Flag Symptoms (Emergency - Administer Epinephrine, Call 911)
- Anaphylaxis: hives with difficulty breathing, throat tightness, or swelling of tongue/lips.
- Severe allergic reaction with hypotension (dizziness, fainting, rapid weak pulse).
- Known severe allergy with accidental exposure and any systemic symptoms.
- Angioedema affecting airway (swelling of lips, tongue, throat).

## Moderate Risk (Physician Evaluation Same Day or Next Day)
- Widespread hives (urticaria) without respiratory compromise.
- Allergic reaction with facial swelling but no airway symptoms.
- Recurrent allergic episodes needing allergy testing referral.
- Drug reaction with rash (non-severe) requiring medication adjustment.

## Low Risk / Self-Care
- Mild seasonal allergies: sneezing, runny nose, itchy eyes.
- Localized contact reaction: small area of redness or itching.
- Recommendation: OTC antihistamines (Cetirizine 10mg or Loratadine 10mg daily), nasal saline spray, avoid known allergens. Seek care if symptoms worsen or OTC medications are inadequate.
""",
}


def seed_database() -> None:
    """Seed the database with doctors, slots, guidelines, and an admin account. Idempotent."""
    db = SessionLocal()
    try:
        _seed_admin(db)
        _seed_doctors(db)
        _seed_slots(db)
        _seed_guidelines()
    except Exception as e:
        print(f"[Seed] Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()


def _seed_admin(db) -> None:
    """Create a default admin account if none exists."""
    existing = db.query(User).filter(User.role == "admin").first()
    if existing:
        return

    admin = User(
        email="admin@petb.health",
        hashed_password=hash_password("admin123"),
        full_name="PETB Admin",
        role="admin",
        preferred_language="en",
    )
    db.add(admin)
    db.commit()
    print("[Seed] Default admin account created (admin@petb.health / admin123).")


def _seed_doctors(db) -> None:
    """Seed 5 specialized doctors if the table is empty."""
    if db.query(Doctor).count() > 0:
        return

    for doc_data in SEED_DOCTORS:
        db.add(Doctor(**doc_data))
    db.commit()
    print(f"[Seed] {len(SEED_DOCTORS)} doctors seeded.")


def _seed_slots(db) -> None:
    """Seed 30+ appointment slots across the next 7 days if the table is empty."""
    if db.query(AppointmentSlot).count() > 0:
        return

    doctors = db.query(Doctor).all()
    if not doctors:
        return

    today = date.today()
    slot_count = 0

    for day_offset in range(1, 8):  # next 7 days
        slot_date = today + timedelta(days=day_offset)
        date_str = slot_date.strftime("%Y-%m-%d")

        # Skip Sundays
        if slot_date.weekday() == 6:
            continue

        for doctor in doctors:
            # Each doctor gets 2-4 slots per day (vary by doctor index)
            doc_idx = doctors.index(doctor)
            start_idx = (doc_idx * 2) % len(SLOT_TIMES)
            num_slots = 2 + (doc_idx % 3)  # 2, 3, or 4 slots

            for i in range(num_slots):
                time_idx = (start_idx + i) % len(SLOT_TIMES)
                start_time, end_time = SLOT_TIMES[time_idx]
                slot = AppointmentSlot(
                    doctor_id=doctor.id,
                    date=date_str,
                    start_time=start_time,
                    end_time=end_time,
                    status="available",
                )
                db.add(slot)
                slot_count += 1

    db.commit()
    print(f"[Seed] {slot_count} appointment slots seeded across next 7 days.")


def _seed_guidelines() -> None:
    """Write clinical guideline text files if they don't already exist."""
    os.makedirs(settings.GUIDELINES_DIR, exist_ok=True)
    created = 0
    for filename, content in GUIDELINE_FILES.items():
        filepath = os.path.join(settings.GUIDELINES_DIR, filename)
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content.strip() + "\n")
            created += 1
    if created:
        print(f"[Seed] {created} guideline file(s) written to {settings.GUIDELINES_DIR}.")
