import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

# Note: Ensure your retrieval.py imports are updated to llama_index.core
from retrieval import RetrievalService
from llama_index.core.schema import NodeWithScore, TextNode

# A simple mock for the Document objects returned by your Vector Store
class MockDoc:
    def __init__(self, text, metadata=None):
        self.page_content = text
        self.metadata = metadata or {}

@pytest.fixture
def mock_deps():
    """Provides mocked embedding and vector store services."""
    embed = MagicMock()
    vstore = MagicMock()
    
    # Setup default vector store return value
    doc1 = MockDoc("Cloud security protocols for RFP", {"doc_type": "pdf"})
    doc2 = MockDoc("Pricing tables for 2024", {"doc_type": "excel"})
    vstore.similarity_search.return_value = [(doc1, 0.95), (doc2, 0.70)]
    
    return embed, vstore

@pytest.fixture
def service(mock_deps):
    embed, vstore = mock_deps
    return RetrievalService(
        embedding_service=embed,
        vector_store_service=vstore,
        rerank=False, # Start with rerank off for basic tests
        score_threshold=0.5
    )

## --- Test Cases ---

def test_successful_search_flow(service, mock_deps):
    """Checks if search returns formatted dicts and filters by score."""
    embed, vstore = mock_deps
    
    # Run search
    results = service.search("security policy", top_k=2)
    
    assert len(results) == 2
    assert results[0]["score"] == 0.95
    assert "content" in results[0]
    vstore.similarity_search.assert_called_once()

def test_score_threshold(service):
    """Ensures documents below the threshold are excluded."""
    service.score_threshold = 0.9
    results = service.search("strict search")
    
    # Only Doc 1 (0.95) should remain; Doc 2 (0.70) is filtered out
    assert len(results) == 1
    assert results[0]["score"] == 0.95

def test_empty_query_error(service):
    """Ensures service handles empty input gracefully."""
    with pytest.raises(ValueError, match="Query cannot be empty"):
        service.search("   ")

@patch("retrieval.FlagEmbeddingReranker")
def test_reranker_integration(mock_reranker_class, service, mock_deps):
    """Verifies that reranking logic is triggered when enabled."""
    service.rerank_enabled = True
    
    # Mock the reranker instance behavior
    mock_inst = MagicMock()
    mock_reranker_class.return_value = mock_inst
    
    # Simulate reranker returning a single node
    mock_node = NodeWithScore(node=TextNode(text="Reranked Content"), score=0.99)
    mock_inst.postprocess_nodes.return_value = [mock_node]
    
    results = service.search("test rerank")
    
    assert len(results) > 0
    mock_inst.postprocess_nodes.assert_called_once()