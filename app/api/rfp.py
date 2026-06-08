from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.rfp_workflows.finalize import finalize_rfp
from app.rfp_workflows.export import export_to_word, export_to_excel

from app.dependencies import (
    get_db, 
    get_retrieval_service, 
    get_llm_service
)
from app.rfp_workflows.storage import parse_file
from app.rfp_workflows.sessions import (
    create_rfp_session,
    add_questions,
    add_question,
    get_rfp,
    get_questions
)

from app.schemas.rfp import (
    RFPSessionCreateRequest,
    RFPSessionResponse,
    QuestionCreateRequest,
    QuestionResponse,
    DraftCreateRequest,
    DraftResponse,
    QuestionListResponse
)
from app.utils.logging import get_logger

logger = get_logger("api.rfp")

# Importing existing logic from rfp_workflows
from app.rfp_workflows import sessions, drafts, finalize
from app.rfp_workflows.drafts import generate_first_draft
from app.knowledge_engine.llm import LLMService
from app.knowledge_engine.retrieval import RetrievalService
from app.knowledge_engine.embeddings import EmbeddingService
from app.knowledge_engine.vector_store import VectorStore

router = APIRouter(prefix="/rfp", tags=["RFP"])


# ---------------------------
# FINALIZE RFP
# ---------------------------
@router.post("/{rfp_id}/finalize")
def finalize(rfp_id: str, db: Session = Depends(get_db)):
    return finalize_rfp(db, rfp_id)


# ---------------------------
# EXPORT WORD
# ---------------------------
@router.get("/{rfp_id}/export/word")
def export_word(rfp_id: str, db: Session = Depends(get_db)):

    file_path = export_to_word(db, rfp_id)

    if not file_path:
        raise HTTPException(status_code=404, detail="No finalized drafts found")

    return {"file": file_path}


# ---------------------------
# EXPORT EXCEL
# ---------------------------
@router.get("/{rfp_id}/export/excel")
def export_excel(rfp_id: str, db: Session = Depends(get_db)):

    file_path = export_to_excel(db, rfp_id)

    if not file_path:
        raise HTTPException(status_code=404, detail="No finalized drafts found")

    return {"file": file_path}


# ---------------------------
# CREATE RFP
# ---------------------------
@router.post("", response_model=RFPSessionResponse)
def create_rfp(
    client_name: str = Form(...),
    deadline: str = Form(...),
    rfp_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service)
):
    logger.info(f"Creating new RFP session for client: {client_name}")
    try:
        deadline_dt = datetime.fromisoformat(deadline)
    except ValueError:
        logger.error(f"Invalid deadline format received: {deadline}")
        raise HTTPException(status_code=400, detail="Invalid deadline format")

    rfp = create_rfp_session(db, client_name, deadline_dt)
    logger.info(f"RFP session created with ID: {rfp.rfp_id}")

    questions = []

    if rfp_file:
        logger.info(f"Parsing uploaded file: {rfp_file.filename}")
        try:
            questions = parse_file(rfp_file, llm_service=llm_service)
            if questions:
                logger.info(f"Extracted {len(questions)} questions from file.")
                add_questions(db, rfp.rfp_id, questions)
        except Exception as e:
            logger.error(f"File parsing failed for {rfp_file.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"File parsing failed: {str(e)}")

    return RFPSessionResponse(
        rfp_id=rfp.rfp_id,
        client_name=rfp.client_name,
        deadline=rfp.deadline
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
        question_id=question.id,
        rfp_id=question.rfp_id,
        question_text=question.question_text,
    )


# -----------------------
# GENERATE DRAFT
# -----------------------
@router.post("/{rfp_id}/question/{question_id}/draft")
def generate_draft(
    rfp_id: str,
    question_id: str,
    db: Session = Depends(get_db),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    llm_service: LLMService = Depends(get_llm_service)
):
    logger.info(f"Generating draft for RFP {rfp_id}, Question {question_id}")

    draft = generate_first_draft(
        db=db,
        question_id=question_id,
        retrieval_service=retrieval_service,
        llm_service=llm_service
    )
    
    logger.info(f"Draft generated successfully: ID {draft.draft_id}")
    return {
        "draft_id": draft.draft_id,
        "question_id": draft.question_id,
        "question_text": draft.question.question_text,
        "answer_text": draft.answer_text,
        "version": draft.version,
        "sources": draft.sources_json
    }

# ---------------------------
# SAVE/UPDATE MANUAL DRAFT
# ---------------------------
@router.post("/draft", response_model=DraftResponse)
@router.put("/draft", response_model=DraftResponse)
def save_manual_draft(
    request: DraftCreateRequest,
    db: Session = Depends(get_db)
):
    # This calls your drafts.add_draft logic
    draft_obj = drafts.add_draft(
        db,
        question_id=request.question_id,
        answer_text=request.answer_text,
        version=request.version
    )
    return draft_obj

# ---------------------------
# REGENERATE AI RESPONSE
# ---------------------------
@router.post("/question/{question_id}/regenerate", response_model=DraftResponse)
@router.post("/{rfp_id}/question/{question_id}/regenerate", response_model=DraftResponse)
def regenerate_response(
    question_id: str,
    rfp_id: str | None = None,
    db: Session = Depends(get_db)
):
    # Initialize RAG Services
    retrieval_service = RetrievalService(
        embedding_service=EmbeddingService(),
        vector_store_service=VectorStore ()
    )
    llm_service = LLMService()

    try:
        # Re-runs the RAG pipeline
        new_draft = generate_first_draft(
            db=db,
            question_id=question_id,
            retrieval_service=retrieval_service,
            llm_service=llm_service
        )
        return new_draft
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {str(e)}")
