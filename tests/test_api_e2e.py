import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import uuid

from app.main import app
from app.db.base import Base
from app.dependencies import (
    get_db, 
    get_embedding_service, 
    get_retrieval_service, 
    get_llm_service,
    Services
)

# ==========================================================
# TEST SETUP
# ==========================================================

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_rfp.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Mock AI Services for stable testing
class MockEmbeddingService:
    def embed_query(self, query):
        return [0.1] * 1024
    def embed_documents(self, docs):
        return {"embeddings": [[0.1]*1024 for _ in docs], "metadatas": [d.metadata for d in docs], "metrics": {"total_chunks": len(docs), "avg_tokens_per_chunk": 10, "min_tokens": 5, "max_tokens": 15, "embedding_dim": 1024, "avg_vector_norm": 1.0, "cache_hit_ratio": 0.0}}

class MockRetrievalService:
    def search(self, query, **kwargs):
        return [
            {
                "content": "Mock context: We use AES-256 encryption.",
                "score": 0.9,
                "metadata": {"source": "mock.pdf"}
            }
        ]

class MockLLMService:
    def generate(self, prompt):
        return "This is a mocked response based on the question."

def override_embedding_service(): return MockEmbeddingService()
def override_retrieval_service(): return MockRetrievalService()
def override_llm_service(): return MockLLMService()

# --- TOGGLE MOCKS BASED ON ENV VAR ---
USE_REAL_AI = os.getenv("USE_REAL_AI", "false").lower() == "true"

if not USE_REAL_AI:
    app.dependency_overrides[get_embedding_service] = override_embedding_service
    app.dependency_overrides[get_retrieval_service] = override_retrieval_service
    app.dependency_overrides[get_llm_service] = override_llm_service
else:
    print("⚠️ RUNNING WITH REAL AI SERVICES. Ensure Ollama and Models are loaded.")

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("./test_rfp.db"):
        try:
            os.remove("./test_rfp.db")
        except PermissionError:
            pass

# ==========================================================
# END-TO-END WORKFLOW TEST
# ==========================================================

def test_rfp_full_workflow():
    # 0. Ingest (Only if real AI is used, to ensure we have context)
    if USE_REAL_AI:
        print("Ingesting knowledge base for real AI test...")
        ingest_resp = client.post("/knowledge/ingest")
        assert ingest_resp.status_code == 200

    # 1. Create RFP
    response = client.post(
        "/rfp",
        data={
            "client_name": "Test Client",
            "deadline": "2025-12-31T23:59:59"
        }
    )
    assert response.status_code == 200
    rfp_data = response.json()
    rfp_id = rfp_data["rfp_id"]
    assert rfp_id is not None

    # 2. Add a question
    response = client.post(
        f"/rfp/{rfp_id}/question",
        json={
            "rfp_id": rfp_id,
            "question_text": "What is your security policy?"
        }
    )
    assert response.status_code == 200
    q_data = response.json()
    question_id = q_data["question_id"]

    # 3. Generate Draft
    response = client.post(f"/rfp/{rfp_id}/question/{question_id}/draft")
    assert response.status_code == 200
    draft_data = response.json()
    assert "answer_text" in draft_data
    assert draft_data["question_id"] == question_id

    # 4. Finalize RFP
    response = client.post(f"/rfp/{rfp_id}/finalize")
    assert response.status_code == 200
    assert response.json()["message"] == "All drafts marked as final"

    # 5. Export Word
    response = client.get(f"/rfp/{rfp_id}/export/word")
    assert response.status_code == 200
    word_file = response.json()["file"]
    assert os.path.exists(word_file)
    os.remove(word_file)

    # 6. Export Excel
    response = client.get(f"/rfp/{rfp_id}/export/excel")
    assert response.status_code == 200
    excel_file = response.json()["file"]
    assert os.path.exists(excel_file)
    os.remove(excel_file)

def test_knowledge_search():
    # If using real AI, this test depends on having ingested data in the REAL vector store
    # For mock testing, it works out of the box.
    response = client.post("/knowledge/search", params={"query": "security"})
    assert response.status_code == 200
    results = response.json()["results"]
    if not USE_REAL_AI:
        assert len(results) > 0
        assert results[0]["content"] == "Mock context: We use AES-256 encryption."
    else:
        print(f"Real AI search returned {len(results)} results")
