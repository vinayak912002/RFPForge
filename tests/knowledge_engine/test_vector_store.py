import os
import shutil
import pytest
from app.knowledge_engine.vector_store import VectorStore


TEST_DB_DIR = "./test_chroma_db"


@pytest.fixture(scope="module")
def vector_store():
    # Clean test DB if exists
    if os.path.exists(TEST_DB_DIR):
        shutil.rmtree(TEST_DB_DIR)

    store = VectorStore(persist_directory=TEST_DB_DIR)
    yield store

    # Cleanup after test
    if os.path.exists(TEST_DB_DIR):
        shutil.rmtree(TEST_DB_DIR, ignore_errors=True)


def test_add_and_get_documents(vector_store):
    documents = ["AES encryption used", "SOC2 compliant"]
    embeddings = [[0.1] * 384, [0.2] * 384]
    metadatas = [
        {"doc_type": "policies"},
        {"doc_type": "compliance_docs"}
    ]

    result = vector_store.add_documents(
        collection_name="test_collection",
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    assert result["count"] == 2

    stored = vector_store.get_documents("test_collection")
    assert len(stored["ids"]) == 2


def test_similarity_search(vector_store):
    query_embedding = [0.1] * 384

    results = vector_store.similarity_search(
        collection_name="test_collection",
        query_embedding=query_embedding,
        k=1
    )

    assert len(results) == 1
    doc, score = results[0]
    assert hasattr(doc, "page_content")
    assert score is not None


def test_health_check(vector_store):
    health = vector_store.health_check("test_collection")

    assert "vector_count" in health
    assert health["vector_count"] >= 0


def test_backup(vector_store):
    result = vector_store.backup_collection("test_collection")

    assert os.path.exists(result["file"])

    os.remove(result["file"])
