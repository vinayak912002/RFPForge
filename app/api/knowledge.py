# ingest, retrieval, draft generation

from fastapi import APIRouter, HTTPException
from app.knowledge_engine.loaders import load_directory
from app.knowledge_engine.chunking import chunk_documents
from app.knowledge_engine.embeddings import EmbeddingService
from app.knowledge_engine.vector_store import VectorStore
from app.knowledge_engine.retrieval import RetrievalService

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


# -----------------------------
# INGEST KNOWLEDGE DOCUMENTS
# -----------------------------
@router.post("/ingest")
def ingest_knowledge():
    try:
        # 1. Load documents
        documents = load_directory("data/knowledge_docs")

        if not documents:
            raise HTTPException(status_code=400, detail="No documents found")

        # 2. Chunk documents
        chunks = chunk_documents(documents)

        # 3. Embeddings
        embedding_service = EmbeddingService()
        vector_store = VectorStore()

        result = embedding_service.embed_documents(chunks)

        # 4. Store in vector DB
        vector_store.add_documents(
            collection_name=vector_store.collection_name,
            documents=[c.page_content for c in chunks],
            embeddings=result["embeddings"],
            metadatas=result["metadatas"]
        )

        return {
            "status": "Knowledge ingested",
            "chunks_created": len(chunks),
            "metrics": result["metrics"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# VECTOR DB HEALTH CHECK
# -----------------------------
@router.get("/health")
def knowledge_health():
    vector_store = VectorStore()
    return vector_store.health_check("rfp_knowledge")


# -----------------------------
# SEARCH KNOWLEDGE BASE
# -----------------------------
@router.post("/search")
def search_knowledge(query: str):
    embedding_service = EmbeddingService()
    vector_store = VectorStore()

    retrieval_service = RetrievalService(
        embedding_service=embedding_service,
        vector_store_service=vector_store
    )

    results = retrieval_service.search(query=query)

    return {
        "query": query,
        "results": results
    }

#  temporary endpoint in knowledge.py for debugging vector store contents. will Remove it later.
@router.get("/debug")
def debug():
    from app.knowledge_engine.vector_store import VectorStore
    vs = VectorStore()
    return vs.get_documents("rfp_knowledge")

# similarly temporary endpoint for testing retrieval end to end. will remove later.
@router.post("/debug-search")
def debug_search(query: str):
    from app.knowledge_engine.embeddings import EmbeddingService
    from app.knowledge_engine.vector_store import VectorStore

    emb = EmbeddingService()
    vs = VectorStore()

    q_emb = emb.embed_query(query)

    results = vs.similarity_search("rfp_knowledge", q_emb, k=5)

    return results

# temporary 
@router.post("/debug-vector-search")
def debug_vector_search(query: str):
    from app.knowledge_engine.embeddings import EmbeddingService
    from app.knowledge_engine.vector_store import VectorStore

    emb = EmbeddingService()
    vs = VectorStore()

    query_embedding = emb.embed_query(query)

    results = vs.similarity_search("rfp_knowledge", query_embedding, k=5)

    return {
        "results": [
            {
                "content": doc.page_content[:200],
                "metadata": doc.metadata,
                "score": score
            }
            for doc, score in results
        ]
    }