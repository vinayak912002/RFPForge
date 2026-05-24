# ingest, retrieval, draft generation

from fastapi import APIRouter, HTTPException, Depends
from app.knowledge_engine.loaders import load_directory
from app.knowledge_engine.chunking import chunk_documents
from app.knowledge_engine.embeddings import EmbeddingService
from app.knowledge_engine.vector_store import VectorStore
from app.knowledge_engine.retrieval import RetrievalService
from app.dependencies import get_embedding_service, get_vector_store, get_retrieval_service
from app.utils.logging import get_logger

logger = get_logger("api.knowledge")

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


# -----------------------------
# INGEST KNOWLEDGE DOCUMENTS
# -----------------------------
@router.post("/ingest")
def ingest_knowledge(
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    vector_store: VectorStore = Depends(get_vector_store)
):
    try:
        logger.info("Starting knowledge ingestion process...")
        # 1. Load documents
        logger.info("Step 1: Loading documents from 'data/knowledge_docs'...")
        documents = load_directory("data/knowledge_docs")

        if not documents:
            logger.warning("No documents found in directory.")
            raise HTTPException(status_code=400, detail="No documents found")

        # 2. Chunk documents
        logger.info(f"Step 2: Chunking {len(documents)} documents...")
        chunks = chunk_documents(documents)

        if not chunks:
             logger.warning("Document loading/cleaning resulted in 0 chunks.")
             return {
                "status": "No chunks created from documents",
                "chunks_created": 0,
                "metrics": {}
            }

        # 3. Embeddings
        logger.info(f"Step 3: Generating embeddings for {len(chunks)} chunks...")
        result = embedding_service.embed_documents(chunks)

        # 4. Store in vector DB
        logger.info(f"Step 4: Storing {len(chunks)} vectors in ChromaDB...")
        vector_store.add_documents(
            collection_name=vector_store.collection_name,
            documents=[c.page_content for c in chunks],
            embeddings=result["embeddings"],
            metadatas=result["metadatas"]
        )

        logger.info("Knowledge ingestion completed successfully.")
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
def knowledge_health(vector_store: VectorStore = Depends(get_vector_store)):
    return vector_store.health_check("rfp_knowledge")


# -----------------------------
# SEARCH KNOWLEDGE BASE
# -----------------------------
@router.post("/search")
def search_knowledge(
    query: str, 
    retrieval_service: RetrievalService = Depends(get_retrieval_service)
):
    results = retrieval_service.search(query=query)

    return {
        "query": query,
        "results": results
    }

#  temporary endpoint in knowledge.py for debugging vector store contents.
@router.get("/debug")
def debug(vector_store: VectorStore = Depends(get_vector_store)):
    return vector_store.get_documents("rfp_knowledge")
