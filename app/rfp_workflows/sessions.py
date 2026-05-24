# session lifecycle

import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from app.rfp_workflows.models import RFPSession, Question, Draft

# 🔹 Create RFP Session
def create_rfp_session(db: Session, client_name: str, deadline: datetime):
    rfp_id = str(uuid.uuid4())

    rfp = RFPSession(
        rfp_id=rfp_id,
        client_name=client_name,
        deadline=deadline,
        status="draft"
    )

    db.add(rfp)
    db.commit()
    db.refresh(rfp)   # ✅ added

    return rfp


# 🔹 Add multiple questions
def add_questions(db: Session, rfp_id: str, questions: list[str]):

    # ✅ check if RFP exists
    rfp = get_rfp(db, rfp_id)
    if not rfp:
        raise ValueError("RFP not found")

    question_objs = []

    for q in questions:
        question = Question(
            id=str(uuid.uuid4()),
            rfp_id=rfp_id,
            question_text=q,
            status="draft"
        )
        question_objs.append(question)

    db.add_all(question_objs)   # ✅ better than loop add
    db.commit()

    return question_objs


# 🔹 Add single question
def add_question(db: Session, rfp_id: str, question_text: str):

    # ✅ validation
    rfp = get_rfp(db, rfp_id)
    if not rfp:
        raise ValueError("RFP not found")

    question = Question(
        id=str(uuid.uuid4()),
        rfp_id=rfp_id,
        question_text=question_text,
        status="draft"
    )

    db.add(question)
    db.commit()
    db.refresh(question)

    return question


# 🔹 Get RFP
def get_rfp(db: Session, rfp_id: str):
    return db.query(RFPSession).filter(RFPSession.rfp_id == rfp_id).first()


# 🔹 Get questions for RFP
def get_questions(db: Session, rfp_id: str):
    return db.query(Question).filter(Question.rfp_id == rfp_id).all()


# =========================================================
# 🔥 NEW: DRAFT FUNCTIONS (MISSING PART)
# =========================================================

# 🔹 Add draft answer
def add_draft(
    db: Session,
    question_id: str,
    answer_text: str,
    version: int,
    edited_by: str = None,
    sources_json: dict = None
):

    # ✅ check if question exists
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise ValueError("Question not found")

    draft = Draft(
        draft_id=str(uuid.uuid4()),
        question_id=question_id,
        answer_text=answer_text,
        version=version,
        edited_by=edited_by,
        sources_json=sources_json
    )

    db.add(draft)
    db.commit()
    db.refresh(draft)

    return draft


# 🔹 Get drafts for a question
def get_drafts(db: Session, question_id: str):
    return db.query(Draft).filter(Draft.question_id == question_id).all()


# 🔹 Get latest draft (VERY USEFUL)
def get_latest_draft(db: Session, question_id: str):
    return (
        db.query(Draft)
        .filter(Draft.question_id == question_id)
        .order_by(Draft.version.desc())
        .first()
    )