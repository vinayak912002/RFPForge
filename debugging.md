# 🔍 Debugging History & Resolutions

This document logs the errors encountered during the development and optimization of the RFP Response Generation Tool, along with their causes and fixes.

---

## 1. Massive Performance Lag / Memory Leaks
*   **Symptoms**: API responses taking 10+ seconds; memory usage spiking on every request.
*   **Cause**: Heavy AI services (specifically `EmbeddingService` which loads a 1.5GB model) were being re-instantiated inside every API endpoint call.
*   **Resolution**: 
    *   Implemented **FastAPI Lifespan** in `main.py` to pre-load models at startup.
    *   Used **Dependency Injection** in `dependencies.py` to provide these services as singletons.

## 2. FileNotFoundError (Absolute Paths)
*   **Symptoms**: Application failed to start or test with an error pointing to `E:\vinayak\...`.
*   **Cause**: Hardcoded absolute paths and test code were left at the module level in `app/knowledge_engine/loaders.py`.
*   **Resolution**: Cleaned up the module-level code and ensured all paths are relative or configurable.

## 3. Metadata Type Mismatch (ChromaDB)
*   **Symptoms**: `500 Internal Server Error` during `/knowledge/ingest`.
*   **Cause**: Attempting to store a `list` (clause numbers) in the ChromaDB metadata. ChromaDB only supports primitive types: `string`, `int`, `float`, and `bool`.
*   **Resolution**: Updated `chunking.py` to serialize the clause list into a comma-separated string using `", ".join()`.

## 4. ZeroDivisionError in Metrics
*   **Symptoms**: Crash during ingestion of small or "noisy" documents.
*   **Cause**: The embedding service was calculating average tokens by dividing by the number of chunks. If zero chunks were generated (due to cleaning filters), it caused a division by zero.
*   **Resolution**: Added safety checks in `embeddings.py` and `knowledge.py` to handle empty chunk scenarios gracefully.

## 5. Pydantic V2 Deprecation Warnings
*   **Symptoms**: Logs cluttered with `PydanticDeprecatedSince20` warnings.
*   **Cause**: The codebase was using V1-style `class Config` blocks while running on Pydantic V2.
*   **Resolution**: Migrated all schemas in `rfp.py` to use `model_config = ConfigDict(from_attributes=True)`.

## 6. datetime.utcnow() Deprecation
*   **Symptoms**: `DeprecationWarning: datetime.datetime.utcnow() is deprecated`.
*   **Cause**: Python 3.12+ deprecated `utcnow()` in favor of timezone-aware objects.
*   **Resolution**: Updated the codebase to use `datetime.now(timezone.utc)`.

## 7. OperationalError: no such column: drafts.edited_by
*   **Symptoms**: `sqlite3.OperationalError: no such column: drafts.edited_by` during draft generation.
*   **Cause**: The Python `Draft` model was updated to include `edited_by`, but the existing `rfp.db` file on disk was created with an older schema. `sqlalchemy` does not automatically migrate existing tables.
*   **Resolution**: Advised deleting the local `rfp.db` file to allow the app to recreate it with the updated schema, or manually running an `ALTER TABLE` SQL command.

## 8. Windows Curl Quoting Issues
*   **Symptoms**: `JSON decode error` and `URL rejected: Bad hostname` when running `curl` from `cmd.exe`.
*   **Cause**: Windows Command Prompt does not recognize single quotes (`'`) for strings. It requires double quotes and escaped internal quotes (`\"`).
*   **Resolution**: Documented the correct Windows syntax in `api_test.md`.

---

## 🛠️ General Debugging Tips
1.  **Check the Console**: Uvicorn prints full tracebacks. Always look at the terminal where the server is running.
2.  **Use Swagger**: If `curl` is giving quoting errors, use `http://127.0.0.1:8000/docs` to test endpoints via the browser.
3.  **Clear Cache**: If you see weird embedding behavior, clear the `./embedding_cache` and `./chroma_db` folders to force a fresh ingestion.
