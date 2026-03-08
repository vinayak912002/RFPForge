# session lifecycle
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from .models import RFPSession, Question


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

    return rfp


def add_questions(db: Session, rfp_id: str, questions: list[str]):
    for q in questions:
        db.add(
            Question(
                id=str(uuid.uuid4()),
                rfp_id=rfp_id,
                question_text=q,
                status="draft"
            )
        )
    db.commit()


def get_rfp(db: Session, rfp_id: str):
    return db.query(RFPSession).filter(RFPSession.rfp_id == rfp_id).first()


def get_questions(db: Session, rfp_id: str):
    return db.query(Question).filter(Question.rfp_id == rfp_id).all()

def add_question(db: Session, rfp_id: str, question_text: str):
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