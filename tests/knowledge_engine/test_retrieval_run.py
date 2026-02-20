
from retrieval import RetrievalService


# -----------------------------
# Mock Document Class
# -----------------------------
class MockDocument:
    def __init__(self, content, metadata):
        self.page_content = content
        self.metadata = metadata


# -----------------------------
# Mock Embedding Service
# -----------------------------
class MockEmbeddingService:
    def embed_query(self, query: str):
        print(f"[Embedding] Query: {query}")
        return [0.1, 0.2, 0.3]  # fake vector


# -----------------------------
# Mock Vector Store Service
# -----------------------------
class MockVectorStoreService:
    def similarity_search(self, query_embedding, k, filter=None):
        print(f"[Vector Search] k={k}")
        print(f"[Vector Search] filter={filter}")

        doc1 = MockDocument(
            "Encryption at rest uses AES-256",
            {"doc_type": "compliance_docs", "section": "security"},
        )

        doc2 = MockDocument(
            "Encryption in transit uses TLS",
            {"doc_type": "compliance_docs", "section": "security"},
        )

        return [
            (doc1, 0.1),
            (doc2, 0.2),
        ]


# -----------------------------
# Run Test
# -----------------------------
if __name__ == "__main__":
    retrieval = RetrievalService(
        embedding_service=MockEmbeddingService(),
        vector_store_service=MockVectorStoreService(),
        score_threshold=0.0,  # disable filtering for demo
    )

    results = retrieval.search(
        query="encryption at rest vs in transit",
        top_k=5,
        doc_type="compliance_docs",
        section="security",
        recency_days=365,
    )

    print("\nFinal Results:\n")
    for r in results:
        print(r)