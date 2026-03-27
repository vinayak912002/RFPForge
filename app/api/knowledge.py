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