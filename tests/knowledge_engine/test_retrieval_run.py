# testing retrieval.py
import pytest
from unittest.mock import MagicMock
from datetime import datetime
from app.knowledge_engine.retrieval import RetrievalService


# --------------------------------------------
# Fake Document Object (like LangChain Document)
# --------------------------------------------

class FakeDocument:
    def __init__(self, content, metadata=None):
        self.page_content = content
        self.metadata = metadata or {}


# --------------------------------------------
# Test Setup Fixture
# --------------------------------------------

@pytest.fixture
def setup_service():
    embedding_service = MagicMock()
    vector_store_service = MagicMock()

    service = RetrievalService(
        embedding_service=embedding_service,
        vector_store_service=vector_store_service,
        score_threshold=0.5,
    )

    return service, embedding_service, vector_store_service


# --------------------------------------------
# 1️⃣ Test Single Query Success
# --------------------------------------------

def test_single_query_success(setup_service):
    service, embedding_service, vector_store_service = setup_service

    embedding_service.embed_query.return_value = [0.1, 0.2]

    fake_doc = FakeDocument("Hello World", {"source": "doc1"})
    vector_store_service.similarity_search.return_value = [
        (fake_doc, 0.9)
    ]

    results = service.search("hello")

    assert len(results) == 1
    assert results[0]["content"] == "Hello World"
    assert results[0]["score"] == 0.9


# --------------------------------------------
# 2️⃣ Test Score Threshold Filtering
# --------------------------------------------

def test_score_threshold_filtering(setup_service):
    service, embedding_service, vector_store_service = setup_service

    embedding_service.embed_query.return_value = [0.1]

    fake_doc = FakeDocument("Low Score", {"source": "doc2"})
    vector_store_service.similarity_search.return_value = [
        (fake_doc, 0.2)  # below threshold (0.5)
    ]

    results = service.search("test")

    assert len(results) == 0


# --------------------------------------------
# 3️⃣ Test Comparison Query Deduplication
# --------------------------------------------

def test_comparison_query_deduplication(setup_service):
    service, embedding_service, vector_store_service = setup_service

    embedding_service.embed_query.return_value = [0.1]

    doc1 = FakeDocument("Same Content", {"source": "docA"})
    doc2 = FakeDocument("Same Content", {"source": "docA"})  # duplicate

    vector_store_service.similarity_search.return_value = [
        (doc1, 0.8),
        (doc2, 0.8),
    ]

    results = service.search("a vs b")

    # Should deduplicate
    assert len(results) == 1


# --------------------------------------------
# 4️⃣ Test Recency Filter Applied
# --------------------------------------------

def test_recency_filter(setup_service):
    service, embedding_service, vector_store_service = setup_service

    embedding_service.embed_query.return_value = [0.1]
    vector_store_service.similarity_search.return_value = []

    service.search("hello", recency_days=5)

    # Check filter passed to vector store
    args, kwargs = vector_store_service.similarity_search.call_args
    assert "filter" in kwargs
    assert "created_at" in kwargs["filter"]


# --------------------------------------------
# 5️⃣ Test Empty Query Raises Error
# --------------------------------------------

def test_empty_query_raises_error(setup_service):
    service, _, _ = setup_service

    with pytest.raises(ValueError):
        service.search("")