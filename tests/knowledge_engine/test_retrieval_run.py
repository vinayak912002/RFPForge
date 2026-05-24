import pytest
from unittest.mock import MagicMock, patch

from app.knowledge_engine.retrieval import RetrievalService


# ------------------------------------------------------------
# Helper: Fake Document Object
# ------------------------------------------------------------

class FakeDocument:
    def __init__(self, content, metadata=None):
        self.page_content = content
        self.metadata = metadata or {}


# ------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------

@pytest.fixture
def mock_embedding_service():
    service = MagicMock()
    service.embed_query.return_value = [0.1, 0.2, 0.3]
    return service


@pytest.fixture
def mock_vector_store():
    store = MagicMock()

    docs = [
        (FakeDocument("Doc A"), 0.8),
        (FakeDocument("Doc B"), 0.6),
        (FakeDocument("Doc C"), 0.4),
    ]

    store.similarity_search.return_value = docs
    return store


# ------------------------------------------------------------
# Test: Basic Search (No Rerank)
# ------------------------------------------------------------

def test_search_without_rerank(mock_embedding_service, mock_vector_store):

    service = RetrievalService(
        embedding_service=mock_embedding_service,
        vector_store_service=mock_vector_store,
        score_threshold=0.5,
        rerank=False,
    )

    results = service.search("test query")

    assert len(results) == 2  # Doc A and Doc B pass threshold
    assert results[0]["score"] >= results[1]["score"]
    mock_embedding_service.embed_query.assert_called_once()
    mock_vector_store.similarity_search.assert_called_once()


# ------------------------------------------------------------
# Test: Empty Query Raises Error
# ------------------------------------------------------------

def test_empty_query_raises(mock_embedding_service, mock_vector_store):

    service = RetrievalService(
        embedding_service=mock_embedding_service,
        vector_store_service=mock_vector_store,
    )

    with pytest.raises(ValueError):
        service.search("")


# ------------------------------------------------------------
# Test: Fake ReRanker 
# ------------------------------------------------------------

class FakeReranker:
    def __init__(self):
        pass

    def compute_score(self, pairs):
        return [0.1, 0.9, 0.2]

# ------------------------------------------------------------
# Test: Failure test 
# ------------------------------------------------------------
class FailingReranker:
    def compute_score(self, pairs):
        raise Exception("Rerank failed")

def test_build_filter(mock_embedding_service, mock_vector_store):

    service = RetrievalService(
        embedding_service=mock_embedding_service,
        vector_store_service=mock_vector_store,
        rerank = True,
        rerank_top_k=2,
        reranker_cls=FakeReranker,  # Inject fake reranker for testing
        )

    filters = service._build_filter(
        doc_type="RFP",
        section="Pricing",
        recency_days=30,
    )

    assert filters["doc_type"] == "rfp"
    assert filters["section"] == "pricing"
    assert "$gte" in filters["created_at"]