# RFPForge Backend API Testing Guide

This guide provides instructions and `curl` commands to manually test each backend endpoint.

## 🏗️ Prerequisites & Setup

### 1. Start Ollama
Ensure Ollama is running and the model is downloaded:
```bash
ollama run llama3.2:3b-instruct-q4_0
```

### 2. Start the FastAPI Server
Run the following command in the project root:
```bash
conda activate RFPForge
uvicorn app.main:app --reload
```
The API will be available at `http://127.0.0.1:8000`. 
Interactive docs (Swagger UI) are at `http://127.0.0.1:8000/docs`.

---

## 📚 Knowledge Base Endpoints

### 1. Ingest Documents
Triggers the ingestion of documents from `data/knowledge_docs` into the vector store.
```bash
curl -X POST http://127.0.0.1:8000/knowledge/ingest
```

### 2. Health Check
Returns metrics about the vector store (vector count, average document length).
```bash
curl -X GET http://127.0.0.1:8000/knowledge/health
```

### 3. Search Knowledge
Search for specific information within the ingested documents.
```bash
curl -X POST "http://127.0.0.1:8000/knowledge/search?query=encryption"
```

### 4. Debug Knowledge
Returns raw documents stored in the vector database.
```bash
curl -X GET http://127.0.0.1:8000/knowledge/debug
```

---

## 🚀 RFP Management Endpoints

### 1. Create RFP Session
Creates a new RFP session. Optionally, you can upload a file (`.pdf`, `.docx`) to extract questions automatically.

**Without File:**
```bash
curl -X POST http://127.0.0.1:8000/rfp \
     -F "client_name=Acme Corp" \
     -F "deadline=2025-12-31T23:59:59"
```

**With File Upload:**
```bash
curl -X POST http://127.0.0.1:8000/rfp \
     -F "client_name=Acme Corp" \
     -F "deadline=2025-12-31T23:59:59" \
     -F "rfp_file=@D:/path/to/your/rfp.pdf"
```

### 2. Get RFP Summary
Get the current status and question count for an RFP.
```bash
# Replace {rfp_id} with actual ID
curl -X GET http://127.0.0.1:8000/rfp/{rfp_id}
```

### 3. List Questions
List all questions extracted or added to a specific RFP.
```bash
curl -X GET http://127.0.0.1:8000/rfp/{rfp_id}/questions
```

### 4. Add Single Question
Manually add a question to an existing RFP session.
```bash
curl -X POST http://127.0.0.1:8000/rfp/{rfp_id}/question \
     -H "Content-Type: application/json" \
     -d '{"rfp_id": "{rfp_id}", "question_text": "How do you handle data backups?"}'
```

### 5. Generate AI Draft
Triggers the RAG pipeline (Retrieval -> Prompting -> LLM) to generate a response for a question.
```bash
curl -X POST http://127.0.0.1:8000/rfp/{rfp_id}/question/{question_id}/draft
```

### 6. Finalize RFP
Marks all generated drafts as "final" so they are ready for export.
```bash
curl -X POST http://127.0.0.1:8000/rfp/{rfp_id}/finalize
```

### 7. Export to Word
Generates and returns the path to a `.docx` file containing finalized responses.
```bash
curl -X GET http://127.0.0.1:8000/rfp/{rfp_id}/export/word
```

### 8. Export to Excel
Generates and returns the path to an `.xlsx` file containing finalized responses.
```bash
curl -X GET http://127.0.0.1:8000/rfp/{rfp_id}/export/excel
```

---

## 🛠️ Testing Tools Recommendation
For a better experience, you can use:
1.  **Swagger UI**: Visit `http://127.0.0.1:8000/docs` in your browser. It allows you to test every endpoint with a graphical interface.
2.  **Postman / Insomnia**: Import the endpoints to organize your tests.
3.  **Real AI E2E Test**: Run `set USE_REAL_AI=true && pytest tests/test_api_e2e.py` for a fully automated test of all the above endpoints.
