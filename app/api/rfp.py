from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.rfp_workflows.models import Base
from app.rfp_workflows.finalize import finalize_rfp
from app.rfp_workflows.export import export_to_word, export_to_excel

DATABASE_URL = "sqlite:///./rfp.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------
# FINALIZE RFP
# ---------------------------
@router.post("/rfp/{rfp_id}/finalize")
def finalize(rfp_id: str, db: Session = Depends(get_db)):
    return finalize_rfp(db, rfp_id)


# ---------------------------
# EXPORT WORD
# ---------------------------
@router.get("/rfp/{rfp_id}/export/word")
def export_word(rfp_id: str, db: Session = Depends(get_db)):

    file_path = export_to_word(db, rfp_id)

    if not file_path:
        raise HTTPException(status_code=404, detail="No finalized drafts found")

    return {
        "file": file_path
    }


# ---------------------------
# EXPORT EXCEL
# ---------------------------
@router.get("/rfp/{rfp_id}/export/excel")
def export_excel(rfp_id: str, db: Session = Depends(get_db)):

    file_path = export_to_excel(db, rfp_id)

    if not file_path:
        raise HTTPException(status_code=404, detail="No finalized drafts found")

    return {
        "file": file_path
    }