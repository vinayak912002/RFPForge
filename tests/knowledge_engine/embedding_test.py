import sys
from pathlib import Path
import tempfile

# Add workspace root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain_core.documents import Document

from app.knowledge_engine.embeddings import (
    load_embedding_model,
    embed_documents,
)

# --------------------------------------------------
# 1️⃣ Sample Chunks (as produced by chunking)
# --------------------------------------------------

chunks = [
    Document(
        page_content="APP As defined in Clause 1.1.2",
        metadata={"source": "test.pdf", "page": 1, "chunk_id": "1"},
    ),
    Document(
        page_content="Bid Due Date As defined in Clause 1.1.7",
        metadata={"source": "test.pdf", "page": 1, "chunk_id": "2"},
    ),
    Document(
        page_content="Tariff As defined in Clause 1.2.6",
        metadata={"source": "test.pdf", "page": 1, "chunk_id": "3"},
    ),
]

# --------------------------------------------------
# 2️⃣ Load embedding model
# --------------------------------------------------

model = load_embedding_model()

print("\nLoading embedding model...")
print(f"Model type: {type(model)}\n")

# --------------------------------------------------
# 3️⃣ Embedding pipeline - First run (no cache)
# --------------------------------------------------

with tempfile.TemporaryDirectory() as tmp_dir:
    cache_dir = Path(tmp_dir) / "embedding_cache"
    
    result_1 = embed_documents(
        documents=chunks,
        model=model,
        cache_dir=cache_dir,
        batch_size=2,
    )

    embeddings_1 = result_1["embeddings"]
    metrics_1 = result_1["metrics"]

    print("--- First run (no cache) ---")
    print(f"First run metrics: {metrics_1}")
    print(f"Number of embeddings: {len(embeddings_1)}")
    print(f"Embedding dimension: {metrics_1.get('embedding_dim', 'N/A')}")
    print(f"Cache hit ratio: {metrics_1.get('cache_hit_ratio', 'N/A')}\n")

    # --------------------------------------------------
    # 4️⃣ Embedding pipeline - Second run (cache hit)
    # --------------------------------------------------

    result_2 = embed_documents(
        documents=chunks,
        model=model,
        cache_dir=cache_dir,
        batch_size=2,
    )

    embeddings_2 = result_2["embeddings"]
    metrics_2 = result_2["metrics"]

    print("--- Second run (with cache) ---")
    print(f"Second run metrics: {metrics_2}")
    print(f"Cache hit ratio: {metrics_2.get('cache_hit_ratio', 'N/A')}\n")

    # --------------------------------------------------
    # 5️⃣ Verify embeddings are identical
    # --------------------------------------------------

    print("--- Verification ---")
    embeddings_match = all(e1 == e2 for e1, e2 in zip(embeddings_1, embeddings_2))
    print(f"Embeddings identical across runs: {embeddings_match}")
    print(f"Sample embedding (first 5 values): {embeddings_1[0][:5]}\n")