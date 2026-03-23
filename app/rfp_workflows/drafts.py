 # draft versioning & edits
import uuid
from sqlalchemy.orm import Session
from app.rfp_workflows.models import Draft, Question


def add_draft(db: Session, question_id: str, answer_text: str, version: int, edited_by=None, sources_json=None):

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


def get_drafts(db: Session, question_id: str):
    return db.query(Draft).filter(Draft.question_id == question_id).all()


def get_latest_draft(db: Session, question_id: str):
    return (
        db.query(Draft)
        .filter(Draft.question_id == question_id)
        .order_by(Draft.version.desc())
        .first()
    )