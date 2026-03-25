# RFP sessions, questions, drafts
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from app.rfp_workflows.drafts import generate_first_draft
from app.knowledge_engine.llm import LLMService
from app.knowledge_engine.retrieval import RetrievalService
from app.knowledge_engine.embeddings import EmbeddingService
from app.knowledge_engine.vector_store import VectorStore

from app.rfp_workflows.storage import SessionLocal, parse_file
from app.rfp_workflows.sessions import (
    create_rfp_session,
    add_questions,
    add_question,
    get_rfp,
    get_questions
)
from app.api.schemas import (
    RFPSessionResponse,
    QuestionListResponse,
    QuestionResponse,
    QuestionCreateRequest
)

router = APIRouter(prefix="/rfp", tags=["RFP"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------
# CREATE RFP
# -----------------------
@router.post("/", response_model=RFPSessionResponse)
async def create_rfp(
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
            add_questions(db, rfp.rfp_id, questions)
        except Exception:
            raise HTTPException(status_code=500, detail="File parsing failed")

    return RFPSessionResponse(
        rfp_id=rfp.rfp_id,
        client_name=rfp.client_name,
        deadline=rfp.deadline,
        status=rfp.status,
        question_count=len(questions)
    )


# -----------------------
# GET RFP SUMMARY
# -----------------------
@router.get("/{rfp_id}", response_model=RFPSessionResponse)
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
@router.get("/{rfp_id}/questions", response_model=QuestionListResponse)
def list_questions(rfp_id: str, db: Session = Depends(get_db)):
    questions = get_questions(db, rfp_id)

    if not questions:
        raise HTTPException(status_code=404, detail="No questions found")

    return QuestionListResponse(
        rfp_id=rfp_id,
        questions=[
            QuestionResponse(
                id=q.id,
                question_text=q.question_text,
                status=q.status
            )
            for q in questions
        ]
    )
# -----------------------
# ADD SINGLE QUESTION
# -----------------------
@router.post("/{rfp_id}/question", response_model=QuestionResponse)
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
        id=question.id,
        question_text=question.question_text,
        status=question.status
    )


@router.post("/{rfp_id}/question/{question_id}/draft")
def generate_draft(
    rfp_id: str,
    question_id: str,
    db: Session = Depends(get_db)
):
    # Initialize services
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
        "answer_text": draft.answer_text,
        "version": draft.version,
        "sources": draft.sources_json
    }