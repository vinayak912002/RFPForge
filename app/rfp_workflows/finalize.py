from sqlalchemy.orm import Session
from app.rfp_workflows.models import Draft, Question


def finalize_rfp(db: Session, rfp_id: str):

    drafts = db.query(Draft).join(Question).filter(
        Question.rfp_id == rfp_id
    ).all()

    if not drafts:
        return {
            "rfp_id": rfp_id,
            "message": "No drafts found"
        }

    for draft in drafts:
        draft.status = "final"

    db.commit()

    return {
        "rfp_id": rfp_id,
        "message": "All drafts marked as final"
    }