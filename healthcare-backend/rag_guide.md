# 📘 RAG Service Explanation & Backend Testing Guide

Welcome! This guide explains what Retrieval-Augmented Generation (RAG) is, how the backend RAG service was built, its current state, and how you can test it like a professional backend engineer.

---

## 💡 1. What is RAG? (Explained Simply)

Imagine you hire a brilliant doctor (an AI Model) who knows general medicine, but you want them to give advice strictly following your hospital's specific clinical guidelines.

Instead of retraining the AI (which is expensive and slow), you give the AI access to a search engine connected to your hospital's handbook. 

**RAG (Retrieval-Augmented Generation)** does exactly this in 3 steps:

1. **Retrieval**: When a user submits symptoms (e.g., *"thunderclap headache"*), the system searches a local vector database for matching pages from your medical guidelines.
2. **Augmentation**: The system attaches those matched medical guidelines to the user's prompt as context.
3. **Generation**: The AI generates a safe, guideline-aligned answer based on the retrieved context.

---

## 🏗️ 2. What Was Built in Your Project

We created a complete **Local RAG Service** in [rag_service.py](file:///C:/projects/PETB/healthcare-backend/rag_service.py) with the following building blocks:

```
[ Medical Guideline Files (.txt) ]
               │
               ▼
[ RecursiveCharacterTextSplitter ] ── (Splits long text into small 500-character chunks)
               │
               ▼
[ HuggingFace Embeddings ]        ── (Converts text chunks into numerical vectors)
               │
               ▼
[ ChromaDB Vector Store ]         ── (Stores vectors locally in ./data/chroma_db)
               │
               ▼
[ get_relevant_context(query) ]   ── (Finds top 3 most relevant context chunks for any symptom)
```

### Components Created:
1. **Medical Guidelines Directory (`./data/guidelines/`)**:
   - [headache_guidelines.txt](file:///C:/projects/PETB/healthcare-backend/data/guidelines/headache_guidelines.txt)
   - [fever_guidelines.txt](file:///C:/projects/PETB/healthcare-backend/data/guidelines/fever_guidelines.txt)
   - [abdominal_pain_guidelines.txt](file:///C:/projects/PETB/healthcare-backend/data/guidelines/abdominal_pain_guidelines.txt)
2. **Knowledge Base Initializer (`initialize_kb()`)**: Reads all guideline `.txt` files, breaks them down into 13 distinct search chunks, creates numerical embeddings using `all-MiniLM-L6-v2`, and persists them into `./data/chroma_db`.
3. **Context Retriever (`get_relevant_context(query, k=3)`)**: Accepts a user query string and retrieves the top 3 relevant guideline chunks.

---

## 🚦 3. Current Project Status: Is It Ready?

- ✅ **`rag_service.py` is 100% complete and fully working!** The local vector database is built and search queries work.
- 🟡 **FastAPI Integration (`main.py`)**: Currently, your `POST /api/chat` route returns hardcoded dummy JSON responses. To make `/docs` test the RAG engine live, `main.py` can call `get_relevant_context()` inside `/api/chat`.

---

## 🧪 4. How to Test This Like a Real Backend Engineer

Here are 3 ways backend engineers test RAG services:

### Method 1: Command-Line Test (Quickest)

Run the standalone RAG service directly from your terminal:

```bash
python rag_service.py
```

**Expected Output:**
```
--- Initializing Knowledge Base ---
Loaded 3 document(s) and split into 13 chunks.
Knowledge base successfully initialized and persisted to '.\data\chroma_db'.

--- Testing Query: 'What should I do if a patient has a severe thunderclap headache with a stiff neck?' ---

[Chunk 1]
## Red Flag Symptoms (Emergency - Immediate ER Evaluation)
- Sudden onset "thunderclap" headache (reaches peak intensity within seconds/minutes).
- Headache accompanied by fever, neck stiffness (nuchal rigidity)...
```

---

### Method 2: Interactive Python REPL Test

Open terminal and launch Python:

```bash
python
```

Then run these lines:

```python
from rag_service import get_relevant_context

# Test query 1: Fever
results = get_relevant_context("Patient has high fever over 103F and stiff neck")
print(results[0])

# Test query 2: Stomach pain
results = get_relevant_context("Severe lower right abdominal pain")
print(results[0])
```

---

### Method 3: Test via FastAPI Swagger UI (`http://127.0.0.1:8000/docs`)

To test via FastAPI Swagger UI:

1. Update [main.py](file:///C:/projects/PETB/healthcare-backend/main.py) to import `get_relevant_context` from `rag_service`.
2. Inside `POST /api/chat`, retrieve context chunks for the user's message.
3. Start the server:
   ```bash
   uvicorn main:app --reload
   ```
4. Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs), expand **POST /api/chat**, click **Try it out**, and enter:
   ```json
   {
     "message": "I have a sudden severe thunderclap headache",
     "language": "en"
   }
   ```
5. Click **Execute** and observe the live retrieved guideline context returned in the API response!

---

## 🎯 Summary Checklist

| Component | Status | How to Verify |
| :--- | :--- | :--- |
| **Guideline Documents** | ✅ Created | Check `./data/guidelines/*.txt` |
| **Vector DB (Chroma)** | ✅ Created | Check `./data/chroma_db/` folder exists |
| **RAG Retrieval Functions** | ✅ Complete | Run `python rag_service.py` |
| **FastAPI Route Integration** | 🔄 Optional Next Step | Connect `rag_service` into `main.py` |
