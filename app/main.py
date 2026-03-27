from fastapi import FastAPI
from app.api import knowledge, rfp
from app.db.base import Base
from app.rfp_workflows.storage import engine

app = FastAPI(
    title="RFPForge API",
    version="1.0.0"
)

# Create tables automatically
Base.metadata.create_all(bind=engine)

app.include_router(rfp.router)
app.include_router(knowledge.router)
    

@app.get("/")
def root():
    return {"message": "RFPForge API is running"}