from typing import Generator
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.knowledge_engine.embeddings import EmbeddingService
from app.knowledge_engine.vector_store import VectorStore
from app.knowledge_engine.retrieval import RetrievalService
from app.knowledge_engine.llm import LLMService

# --- DATABASE DEPENDENCY ---
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- SERVICE SINGLETONS ---
# These will be initialized once by the lifespan event in main.py

class Services:
    embedding_service: EmbeddingService = None
    vector_store: VectorStore = None
    retrieval_service: RetrievalService = None
    llm_service: LLMService = None

def get_embedding_service() -> EmbeddingService:
    if Services.embedding_service is None:
        Services.embedding_service = EmbeddingService()
    return Services.embedding_service

def get_vector_store() -> VectorStore:
    if Services.vector_store is None:
        Services.vector_store = VectorStore()
    return Services.vector_store

def get_retrieval_service() -> RetrievalService:
    if Services.retrieval_service is None:
        Services.retrieval_service = RetrievalService(
            embedding_service=get_embedding_service(),
            vector_store_service=get_vector_store()
        )
    return Services.retrieval_service

def get_llm_service() -> LLMService:
    if Services.llm_service is None:
        Services.llm_service = LLMService()
    return Services.llm_service
