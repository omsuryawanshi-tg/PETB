# 🦙 Ollama LLM Integration & Backend Testing Guide

Welcome! This guide explains what was built to integrate a local Large Language Model (LLM) using **Ollama** and **qwen2.5:7b** into your Healthcare Triage backend, how it works, and how to test it like a professional backend engineer.

---

## 💡 1. What Was Built & How It Works (Explained Simply)

Previously, your backend used static dummy text to reply to patient queries. 

Now, your backend has a **real AI brain** running 100% locally on your computer using **Ollama** and the **`qwen2.5:7b`** model!

### The Complete AI Triage Workflow:

```
[ 1. User Message ] ──> (e.g. "Severe thunderclap headache in Spanish")
         │
         ▼
[ 2. Local RAG Search ] ──> (Retrieves top 3 matching medical guidelines from ChromaDB)
         │
         ▼
[ 3. LangChain Prompt ] ──> (Combines guidelines + symptoms + medical nurse system role)
         │
         ▼
[ 4. Ollama (qwen2.5:7b) ] ──> (Generates clinical triage evaluation in strict JSON)
         │
         ▼
[ 5. FastAPI Response ] ──> (Returns severity, recommendation, and response_message)
```

---

## 🛠️ 2. Key Components Added in `main.py`

1. **`langchain-ollama` Integration**:
   ```python
   from langchain_ollama import OllamaLLM

   llm = OllamaLLM(model="qwen2.5:7b", format="json")
   ```
2. **Medical Triage Nurse System Prompt**:
   - Instructs the AI model to act as a **clinical triage nurse**.
   - Evaluates patient symptoms strictly against the **RAG guidelines context**.
   - Requires JSON output with 3 keys: `severity`, `recommendation`, and `response_message`.
   - Generates the response in the **patient's requested language** (e.g., English, Spanish, Hindi, French).
3. **Resilient JSON Parser & Fallback Mechanism**:
   - Parses the JSON returned by the model.
   - If Ollama is temporarily stopped or encounters an error, the backend automatically uses a safe fallback so the API never crashes.

---

## 🚦 3. Current Project Status: Is It Ready?

- ✅ **100% Complete & Integrated in `main.py`!**
- The backend is ready to receive requests via `POST /api/chat`, query ChromaDB for context, pass data to Ollama `qwen2.5:7b`, and return JSON.

---

## 🧪 4. How to Test This Like a Real Backend Engineer

Follow these 4 steps to test your live Ollama integration:

### Step 1: Ensure Ollama is Running & Model is Available

Open a terminal window and verify that Ollama is running:

```bash
ollama list
```

You should see `qwen2.5:7b` in the list. If you haven't pulled it yet, run:

```bash
ollama pull qwen2.5:7b
```

---

### Step 2: Start the FastAPI Server

In your backend directory (`C:\projects\PETB\healthcare-backend`), start Uvicorn:

```bash
uvicorn main:app --reload
```

---

### Step 3: Test via Swagger UI (`http://127.0.0.1:8000/docs`)

1. Open **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** in your web browser.
2. Click on **`POST /api/chat`** ➔ **Try it out**.

#### Test Case A: Emergency Symptom (English)
**Request Body:**
```json
{
  "message": "I suddenly developed an extreme thunderclap headache with a very stiff neck and high fever.",
  "language": "en"
}
```
**Expected Response:**
- `severity`: `"Emergency"` or `"High"`
- `recommendation`: Guidance to seek immediate emergency ER evaluation.
- `relevant_context`: Contains the retrieved `headache_guidelines.txt` and `fever_guidelines.txt` chunks.

#### Test Case B: Multilingual Test (Spanish)
**Request Body:**
```json
{
  "message": "Tengo un dolor de cabeza muy fuerte y fiebre alta.",
  "language": "es"
}
```
**Expected Response:**
- `response_message`: Written in natural **Spanish** by `qwen2.5:7b`!

---

### Step 4: Test via Command-Line (`curl`)

You can also test directly using `curl` from terminal:

```bash
curl -X POST "http://127.0.0.1:8000/api/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Mild stomach ache after dinner", "language": "en"}'
```

---

## 🎯 Quick Summary Table

| Feature | Status | Technology Used |
| :--- | :--- | :--- |
| **Local LLM Execution** | ✅ Ready | Ollama + `qwen2.5:7b` |
| **LangChain Integration** | ✅ Ready | `langchain-ollama` & `PromptTemplate` |
| **Medical RAG Context** | ✅ Ready | ChromaDB + `sentence-transformers` |
| **FastAPI Swagger API Docs** | ✅ Ready | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) |
