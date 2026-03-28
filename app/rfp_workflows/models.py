from sqlalchemy import Column, String, Text, Integer, JSON
from app.db.base import Base


class Draft(Base):
    __tablename__ = "drafts"

    draft_id = Column(String, primary_key=True)
    rfp_id = Column(String)
    question_id = Column(String)

    answer_text = Column(Text)
    sources_json = Column(JSON)
    retrieval_snapshot = Column(JSON)

    version = Column(Integer, default=1)
    status = Column(String, default="draft")