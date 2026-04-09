from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import Optional

from app.rfp_workflows.models import Base
from app.rfp_workflows.finalize import finalize_rfp
from app.rfp_workflows.export import export_to_word, export_to_excel

from app.db.dependencies import get_db
from app.rfp_workflows.storage import parse_file
from app.rfp_workflows.sessions import (
    create_rfp_session,
    add_questions,
    add_question,
    get_rfp,
    get_questions
)

from app.schemas.rfp import (
    RFPSessionResponse,
    QuestionListResponse,
    QuestionResponse,
    QuestionCreateRequest
)

from app.rfp_workflows.drafts import generate_first_draft
from app.knowledge_engine.llm import LLMService
from app.knowledge_engine.retrieval import RetrievalService
from app.knowledge_engine.embeddings import EmbeddingService
from app.knowledge_engine.vector_store import VectorStore


DATABASE_URL = "sqlite:///./rfp.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False})
  
SessionLocal = sessionmaker(bind=engine)

SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

router = APIRouter()


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

    return {"file": file_path}


# ---------------------------
# EXPORT EXCEL
# ---------------------------
@router.get("/rfp/{rfp_id}/export/excel")
def export_excel(rfp_id: str, db: Session = Depends(get_db)):

    file_path = export_to_excel(db, rfp_id)

    if not file_path:
        raise HTTPException(status_code=404, detail="No finalized drafts found")

    return {"file": file_path}


# ---------------------------
# CREATE RFP
# ---------------------------
@router.post("/rfp", response_model=RFPSessionResponse)
def create_rfp(
    client_name: str = Form(...),
    deadline: str = Form(...),
    rfp_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    try:
        deadline_dt = datetime.fromisoformat(deadline)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid deadline format")

    rfp = create_rfp_session(db, client_name, deadline_dt)

    questions = []

    if rfp_file:
        try:
            questions = parse_file(rfp_file)
            if questions:
                add_questions(db, rfp.rfp_id, questions)
        except Exception:
            raise HTTPException(status_code=500, detail="File parsing failed")

    return RFPSessionResponse(
        rfp_id=rfp.rfp_id,
        client_name=rfp.client_name,
        deadline=rfp.deadline
    )


# -----------------------
# GET RFP SUMMARY
# -----------------------
@router.get("/rfp/{rfp_id}", response_model=RFPSessionResponse)
def get_rfp_summary(rfp_id: str, db: Session = Depends(get_db)):
    rfp = get_rfp(db, rfp_id)

    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")

    questions = get_questions(db, rfp_id)

    return RFPSessionResponse(
        rfp_id=rfp.rfp_id,
        client_name=rfp.client_name,
        deadline=rfp.deadline,
        status=rfp.status,
        question_count=len(questions)
    )


# -----------------------
# GET QUESTIONS
# -----------------------
@router.get("/rfp/{rfp_id}/questions", response_model=QuestionListResponse)
def list_questions(rfp_id: str, db: Session = Depends(get_db)):
    questions = get_questions(db, rfp_id)

    return QuestionListResponse(
        rfp_id=rfp_id,
        questions=[
            QuestionResponse(
                question_id=q.id,
                rfp_id=q.rfp_id,
                question_text=q.question_text,
            )
            for q in questions
        ]
    )


# -----------------------
# ADD SINGLE QUESTION
# -----------------------
@router.post("/rfp/{rfp_id}/question", response_model=QuestionResponse)
def add_single_question(
    rfp_id: str,
    request: QuestionCreateRequest,
    db: Session = Depends(get_db)
):

    rfp = get_rfp(db, rfp_id)

    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")

    question = add_question(db, rfp_id, request.question_text)

    return QuestionResponse(
        question_id=question.id,
        rfp_id=question.rfp_id,
        question_text=question.question_text,
    )


# -----------------------
# GENERATE DRAFT
# -----------------------
@router.post("/rfp/{rfp_id}/question/{question_id}/draft")
def generate_draft(
    rfp_id: str,
    question_id: str,
    db: Session = Depends(get_db)
):

    embedding_service = EmbeddingService()
    vector_store = VectorStore()

    retrieval_service = RetrievalService(
        embedding_service=embedding_service,
        vector_store_service=vector_store
    )

    llm_service = LLMService()

    draft = generate_first_draft(
        db=db,
        question_id=question_id,
        retrieval_service=retrieval_service,
        llm_service=llm_service
    )

    return {
        "draft_id": draft.draft_id,
        "question_id": draft.question_id,
        "question_text": draft.question.question_text,
        "answer_text": draft.answer_text,
        "version": draft.version,
        "sources": draft.sources_json
    }