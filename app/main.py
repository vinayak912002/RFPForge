from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api import knowledge, rfp
from app.db.session import init_db
from app.dependencies import get_embedding_service, get_retrieval_service, get_llm_service
from app.utils.logging import setup_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize logging, DB and heavy services
    setup_logging()
    print("Initializing Database...")
    init_db()
    
    print("Pre-loading heavy AI models...")
    # This triggers the singleton initialization
    get_embedding_service()
    get_retrieval_service()
    get_llm_service()
    
    print("RFPForge API is ready.")
    yield
    # Shutdown: Clean up if needed
    print("Shutting down...")

app = FastAPI(title="RFPForge API", lifespan=lifespan)

# Include routers
app.include_router(rfp.router)
app.include_router(knowledge.router)

@app.get("/")
def root():
    return {"message": "RFPForge API is running"}
