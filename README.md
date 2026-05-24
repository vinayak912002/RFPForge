# RFPForge 🚀

RFPForge is a specialized, AI-powered backend system designed to automate and streamline the Request for Proposal (RFP) response process. By leveraging a local Large Language Model (LLM) and Retrieval-Augmented Generation (RAG), RFPForge ingests your company's knowledge base and intelligently drafts precise, context-aware answers to client questionnaires.

---

## 🌟 Key Features

*   **Intelligent Knowledge Ingestion**: Automatically parses and chunks company documents (PDFs, Word docs, Text) into a searchable vector database.
*   **Automated Draft Generation**: Uses Local AI (Ollama) to synthesize answers based purely on your ingested corporate knowledge, minimizing hallucinations.
*   **Session Management**: Create distinct RFP sessions, track deadlines, and manage client metadata.
*   **Document Parsing**: Upload client RFP documents directly; the system extracts questions automatically.
*   **Draft Iteration & Finalization**: Generate, review, and finalize multiple drafts per question.
*   **One-Click Exports**: Instantly compile finalized answers into professionally formatted `.docx` (Word) or `.xlsx` (Excel) files.
*   **100% Local & Private**: Powered by local LLMs (Llama 3.2 via Ollama) and local embeddings (ChromaDB), ensuring your sensitive corporate data never leaves your infrastructure.

---

## 🏗️ Architecture & Tech Stack

*   **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
*   **Database**: SQLite (via SQLAlchemy) for relational data (RFPs, Questions, Drafts).
*   **Vector Store**: [ChromaDB](https://www.trychroma.com/) for fast similarity search and document retrieval.
*   **Local AI Provider**: [Ollama](https://ollama.com/) running `llama3.2:3b-instruct-q4_0`.
*   **Embeddings & Reranking**: `sentence-transformers` and `FlagEmbedding` (BGE Reranker) for highly accurate context retrieval.
*   **Document Processing**: `unstructured`, `PyPDF2`, `python-docx`, and LangChain text splitters.

---

## ⚙️ Getting Started

### 1. Prerequisites

*   **Python**: 3.12+ recommended.
*   **Conda**: Strongly recommended for environment management.
*   **Ollama**: Installed and running locally.

### 2. Environment Setup

Create and activate a new Conda environment:
```bash
conda create -n RFPForge python=3.12
conda activate RFPForge
```

Install the required dependencies. Note the use of the legacy resolver to ensure package compatibility:
```bash
pip install -r requirements.txt --use-deprecated=legacy-resolver
```

### 3. Local AI Setup

Ensure Ollama is running and pull the required instruction-tuned model:
```bash
ollama run llama3.2:3b-instruct-q4_0
```

---

## 🚀 Running the Application

Start the FastAPI server using Uvicorn:

```bash
uvicorn app.main:app --reload
```

The application will be accessible at:
*   **API Base URL**: `http://127.0.0.1:8000`
*   **Interactive API Docs (Swagger UI)**: `http://127.0.0.1:8000/docs`

---

## 🧪 Testing Guide

RFPForge includes a robust test suite covering both isolated logic and full real-AI integration.

### Run Fast E2E Tests (Mocked AI)
The default test suite uses dependency injection to mock the LLM and vector stores, allowing for rapid testing of business logic.
```bash
pytest
```

### Run Integration Tests (Real AI)
To test the complete RAG pipeline connecting to your local Ollama instance and ChromaDB:
```bash
# On Windows (PowerShell)
$env:USE_REAL_AI="true"; pytest tests/test_api_e2e.py

# On Linux/macOS
USE_REAL_AI=true pytest tests/test_api_e2e.py
```

---

## 📁 Project Structure

```text
├── app/                  # FastAPI Application Core
│   ├── api/              # Route endpoints (RFP management, Knowledge ingestion)
│   ├── knowledge_engine/ # RAG pipeline, Embeddings, ChromaDB integration
│   ├── rfp_workflows/    # Business logic for drafts and document generation
│   └── main.py           # Application entry point
├── data/                 # Local data storage (Knowledge Docs, Vector DB)
├── tests/                # Pytest suite (Unit & E2E tests)
├── requirements.txt      # Python dependencies
└── README.md             # This document
```

---

## 📚 API Overview

Here are a few core workflows available via the API. (See `http://localhost:8000/docs` for the complete schema).

1.  **Ingest Knowledge**: `POST /knowledge/ingest`
2.  **Create RFP**: `POST /rfp`
3.  **Generate Draft**: `POST /rfp/{rfp_id}/question/{question_id}/draft`
4.  **Export Answers**: `GET /rfp/{rfp_id}/export/word`
