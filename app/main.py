from fastapi import FastAPI
from app.api.rfp import router as rfp_router

app = FastAPI(title="RFPForge API")

app.include_router(rfp_router)