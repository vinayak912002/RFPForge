"""
Manual test runner for RetrievalService
"""

import sys
import os

# --------------------------------------------------
# Add project root to Python path
# --------------------------------------------------
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
sys.path.append(PROJECT_ROOT)

# Now we can import retrieval properly
from app.knowledge_engine.retrieval import RetrievalService


# --------------------------------------------------
# Mock Document
# --------------------------------------------------
class MockDocument:
    def __init__(self, content, metadata):
        self.page_content = content
        self.metadata = metadata


# --------------------------------------------------
# Mock Embedding Service
# --------------------------------------------------
class MockEmbeddingService:
    def embed_query(self, query: str):
        print(f"\n[Embedding Service] Called with query: {query}")
        return [0.1, 0.2, 0.3]  # fake embedding vector


# --------------------------------------------------
# Mock Vector Store Service
# --------------------------------------------------
class MockVectorStoreService:
    def similarity_search(self, query_embedding, k, filter=None):
        print(f"\n[Vector Store] similarity_search called")
        print(f"Top K: {k}")
        print(f"Filter applied: {filter}")

        doc1 = MockDocument(
            "Encryption at rest uses AES-256 encryption.",
            {"doc_type": "compliance_docs", "section": "security"},
        )

        doc2 = MockDocument(
            "Encryption in transit uses TLS 1.3.",
            {"doc_type": "compliance_docs", "section": "security"},
        )

        return [
            (doc1, 0.1),  # high similarity
            (doc2, 0.2),
        ]


# --------------------------------------------------
# Run Test
# --------------------------------------------------
if __name__ == "__main__":

    retrieval = RetrievalService(
        embedding_service=MockEmbeddingService(),
        vector_store_service=MockVectorStoreService(),
        score_threshold=0.0,  # disable threshold for testing
    )

    print("\n==============================")
    print("Running Retrieval Test")
    print("==============================")

    results = retrieval.search(
        query="encryption at rest vs in transit",
        top_k=5,
        doc_type="compliance_docs",
        section="security",
        recency_days=365,
    )

    print("\n==============================")
    print("Final Results")
    print("==============================")

    for r in results:
        print(r)