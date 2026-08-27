# Multi-Turn Triage Agent & Tool Calling Guide

This guide covers the **multi-turn conversational agent** update: what changed, how it works, and how to test everything in the browser using **FastAPI Swagger UI** only.

---

## 1. What Was Built

Previously, `POST /api/chat` took a single `message` string, ran one RAG + LLM triage call, and returned `severity` / `recommendation` / `response_message`.

Now the chat endpoint is a **multi-turn agent** that:

1. Accepts full conversation history (`messages`)
2. Uses **local Qwen 2.5** via Ollama (`ChatOllama`)
3. Can **call tools** mid-conversation to check slots and book appointments
4. Returns a frontend-friendly envelope: message + optional booking redirect

```
[ Swagger / Frontend ]
        │
        │  POST /api/chat  { messages, patient_name, language }
        ▼
[ main.py ]
        │
        │  run_triage_agent(...)
        ▼
[ agent.py ]
   ├─ RAG context (rag_service) injected into system prompt
   ├─ ChatOllama (qwen2.5:3b) + tool-calling loop
   ├─ Tool: check_slots(day_or_date)     → SQLite available slots
   └─ Tool: book_appointment_slot(...)   → mark slot booked
        │
        ▼
[ JSON ]  response_message, action, booking_details?
```

---

## 2. Files Changed / Added

| File | Change |
| :--- | :--- |
| **`agent.py`** *(new)* | Tools + system prompt + `run_triage_agent()` tool-calling loop |
| **`main.py`** *(updated)* | New `ChatRequest` / `ChatResponse`; `/api/chat` calls the agent |
| **Unchanged** | `GET /api/appointments/slots`, `POST /api/appointments/book`, `models.py`, `database.py`, RAG files |

### New request body (`ChatRequest`)

```json
{
  "messages": [
    { "role": "user", "content": "I have a fever and headache" }
  ],
  "patient_name": "Jane Doe",
  "language": "en"
}
```

| Field | Type | Purpose |
| :--- | :--- | :--- |
| `messages` | `list[dict]` | Full chat history; each item needs `role` (`user` / `assistant`) and `content` |
| `patient_name` | `string` | Used when booking; also told to the model in the system prompt |
| `language` | `string` | Response language (default `"en"`) |

### New response body (`ChatResponse`)

```json
{
  "response_message": "Based on your symptoms...",
  "action": "NONE",
  "booking_details": null
}
```

After a successful booking:

```json
{
  "response_message": "You're booked with Dr. Williams on 2026-08-16 at 10:00 AM.",
  "action": "REDIRECT_TO_CONFIRMATION",
  "booking_details": {
    "appointment_id": 4,
    "doctor_id": "DOC-103",
    "date": "2026-08-16",
    "time_slot": "10:00 AM"
  }
}
```

| `action` value | Meaning |
| :--- | :--- |
| `NONE` | Normal chat reply (triage advice, asking for a day, listing slots, etc.) |
| `REDIRECT_TO_CONFIRMATION` | Booking succeeded; frontend should show confirmation using `booking_details` |

### Agent tools (internal — not separate HTTP endpoints)

| Tool | What it does |
| :--- | :--- |
| `check_slots(day_or_date)` | Queries SQLite for `status == 'available'` matching a day name or date (e.g. `"Saturday"`, `"2026-08-15"`, `"August 16"`). Returns slot IDs, doctor names, dates, times. |
| `book_appointment_slot(slot_id, patient_name)` | Sets that row to `booked`, stores `patient_name`, returns confirmation details. |

Doctor IDs map to display names in `agent.py`: DOC-101 → Dr. Smith, DOC-102 → Dr. Johnson, DOC-103 → Dr. Williams.

---

## 3. Prerequisites Before Testing

1. **Ollama running** with the model pulled:
   ```bash
   ollama serve
   ollama pull qwen2.5:3b
   ```
2. **Backend running** from the project folder:
   ```bash
   uvicorn main:app --reload
   ```
3. Open Swagger in the browser: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

> First `/api/chat` call can be slow (model + RAG load). Later calls are usually faster.

### Optional: reset appointment data

If slots were already booked in earlier tests:

1. Stop the server (`Ctrl+C`)
2. Delete `triage.db`
3. Restart `uvicorn main:app --reload`  
   → seeder recreates 5 available slots for **2026-08-15** and **2026-08-16**

Seeded slots:

| ID | Date | Time | Doctor |
| :---: | :--- | :--- | :--- |
| 1 | 2026-08-15 | 09:00 AM | DOC-101 |
| 2 | 2026-08-15 | 11:30 AM | DOC-101 |
| 3 | 2026-08-15 | 02:00 PM | DOC-102 |
| 4 | 2026-08-16 | 10:00 AM | DOC-103 |
| 5 | 2026-08-16 | 03:30 PM | DOC-103 |

---

## 4. Swagger Test Plan (Browser Only)

Use the **Try it out** flow on each endpoint. For multi-turn chat, **copy the previous assistant reply** into the next request’s `messages` array so the agent keeps context.

---

### Step A — Sanity check: list slots

1. Expand **`GET /api/appointments/slots`**
2. Click **Try it out** → **Execute**
3. Expect status **200** and an array of available slots (IDs, dates, times, `doctor_id`)

Keep this open in another tab if you want — after booking via chat, that slot should disappear from this list.

---

### Step B — Turn 1: symptoms only (no booking yet)

1. Expand **`POST /api/chat`**
2. Click **Try it out**
3. Paste this body:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "I have had a high fever and a bad headache for two days."
    }
  ],
  "patient_name": "Jane Doe",
  "language": "en"
}
```

4. Click **Execute**

**What to expect**

- Status **200**
- `response_message`: empathetic triage advice; for moderate symptoms it should recommend seeing a doctor and ask for a preferred day
- `action`: `"NONE"`
- `booking_details`: `null`

Copy the `response_message` text for the next turn.

---

### Step C — Turn 2: patient picks a day (triggers `check_slots`)

1. Same endpoint **`POST /api/chat`**
2. Paste a body that includes **both** prior turns (replace the assistant text with what you got in Step B):

```json
{
  "messages": [
    {
      "role": "user",
      "content": "I have had a high fever and a bad headache for two days."
    },
    {
      "role": "assistant",
      "content": "PASTE_THE_response_message_FROM_STEP_B_HERE"
    },
    {
      "role": "user",
      "content": "Do you have anything on August 16?"
    }
  ],
  "patient_name": "Jane Doe",
  "language": "en"
}
```

You can also try day names that match the seed dates, e.g. `"Saturday"` (2026-08-15) or `"2026-08-16"`.

**What to expect**

- `response_message` lists real slots (IDs, doctor names, times) from SQLite — not invented times
- `action`: `"NONE"`
- Note a **slot_id** you want to book (e.g. `4` or `5`)

---

### Step D — Turn 3: patient selects a slot (triggers `book_appointment_slot`)

1. Same endpoint again; append the previous assistant reply and a selection message:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "I have had a high fever and a bad headache for two days."
    },
    {
      "role": "assistant",
      "content": "PASTE_STEP_B_REPLY"
    },
    {
      "role": "user",
      "content": "Do you have anything on August 16?"
    },
    {
      "role": "assistant",
      "content": "PASTE_STEP_C_REPLY"
    },
    {
      "role": "user",
      "content": "Please book slot 5 for me."
    }
  ],
  "patient_name": "Jane Doe",
  "language": "en"
}
```

**What to expect**

- `action`: `"REDIRECT_TO_CONFIRMATION"`
- `booking_details` filled, for example:

```json
{
  "appointment_id": 5,
  "doctor_id": "DOC-103",
  "date": "2026-08-16",
  "time_slot": "03:30 PM"
}
```

- `response_message` confirms the booking for Jane Doe

---

### Step E — Verify booking stuck in the database (still via Swagger)

1. Run **`GET /api/appointments/slots`** again  
   → the booked ID (e.g. `5`) should **no longer** appear
2. Optional: try **`POST /api/appointments/book`** with the same ID — expect **400** (already booked)

Direct book body (for comparison with the agent path):

```json
{
  "appointment_id": 4,
  "patient_name": "Jane Doe"
}
```

---

### Step F — Emergency path (no booking)

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Sudden thunderclap headache and I feel like I might pass out."
    }
  ],
  "patient_name": "Jane Doe",
  "language": "en"
}
```

**Expect:** urgent ER / emergency advice, `action: "NONE"`, no booking.

---

## 5. Common Swagger Mistakes

| Mistake | Fix |
| :--- | :--- |
| Still sending old body `{ "message": "..." }` | Use `messages` (array), plus `patient_name` and `language` |
| Only sending the latest user line | Include full history: user → assistant → user → … |
| Expecting instant first response | Cold start of Ollama + embeddings can take a while |
| No slots returned for a day | Use seed dates `2026-08-15` / `2026-08-16`, or reset `triage.db` |
| Booking fails | Slot already booked — reset DB or pick another `slot_id` from Step C |

---

## 6. Quick Checklist

- [ ] Ollama up with `qwen2.5:3b`
- [ ] `uvicorn main:app --reload` → [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- [ ] `GET /api/appointments/slots` returns available rows
- [ ] Turn 1 chat → triage advice, `action: NONE`
- [ ] Turn 2 with a day → real slots listed
- [ ] Turn 3 with a slot ID → `REDIRECT_TO_CONFIRMATION` + `booking_details`
- [ ] Slots endpoint no longer shows the booked ID

---

## 7. Summary

| Before | After |
| :--- | :--- |
| Single `message` string | `messages[]` conversation history |
| One-shot triage JSON (`severity`, etc.) | Agent reply + `action` + optional `booking_details` |
| Book only via separate HTTP endpoint | Agent can check/book mid-chat via tools (REST book endpoint still works) |
| `OllamaLLM` JSON mode | `ChatOllama` with LangChain tool calling |
