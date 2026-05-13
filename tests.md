# Testing Guide for RFP Response Generation Tool

This document explains how to run tests and verify the functionality of the RFP tool.

## 🏗️ Setup
Ensure you have the development dependencies installed:
```bash
pip install pytest httpx
```

## 🧪 Running Tests

### 1. End-to-End (E2E) Tests
The E2E tests verify the complete workflow. By default, they use **mocks** for AI services to be fast and environment-independent.

**Run with Mocks (Logic Check):**
```bash
pytest tests/test_api_e2e.py
```

**Run with Real AI (Integration Check):**
To verify that Ollama, Embeddings, and the Vector Store are working correctly:
```bash
# Windows (PowerShell)
$env:USE_REAL_AI="true"; pytest tests/test_api_e2e.py

# Windows (Command Prompt)
set USE_REAL_AI=true && pytest tests/test_api_e2e.py
```
*Note: Real AI tests require Ollama to be running and models to be downloaded.*

### 2. Unit & Component Tests
The codebase contains several component-level tests for the knowledge engine and rfp workflows.

*   **Knowledge Engine Tests:**
    ```bash
    pytest tests/knowledge_engine/
    ```
*   **Workflow Tests:**
    ```bash
    pytest tests/rfp_workflows/
    ```

### 3. Running All Tests
To run the entire test suite:
```bash
pytest
```

---

## 🔍 What is Covered?

### API Workflows (`tests/test_api_e2e.py`)
- **RFP Creation**: Validates session initialization.
- **Question Management**: Adding single questions and parsing files.
- **Draft Generation**: Verifies the link between retrieval, LLM, and versioning.
- **Finalization**: Marking drafts as ready for export.
- **Exporting**: Ensures `.docx` and `.xlsx` files are generated correctly.

### Knowledge Engine (`tests/knowledge_engine/`)
- **Chunking**: Tests different chunking modes (Structured, Semi-structured).
- **Embeddings**: Verifies vector generation and caching.
- **Retrieval**: Tests similarity search and BGE reranking.

---

## 🛠️ Debugging Tests
If a test fails, you can see more details using:
```bash
pytest -vv -s
```

## 📝 Mocking Note
The E2E tests use `app.dependency_overrides` to swap real AI models with fast, predictable mocks. This allows for rapid testing of the application logic and database integrity without external dependencies.
