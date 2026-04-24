from sqlalchemy import Column, String, Text, Integer, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


# ---------------------------
# RFP SESSION
# ---------------------------
class RFPSession(Base):
    __tablename__ = "rfp_sessions"

    rfp_id = Column(String, primary_key=True)
    client_name = Column(String, nullable=False)
    deadline = Column(DateTime, nullable=False)
    status = Column(String, default="draft")

    questions = relationship("Question", back_populates="rfp")


# ---------------------------
# QUESTION
# ---------------------------
class Question(Base):
    __tablename__ = "questions"

    id = Column(String, primary_key=True)
    rfp_id = Column(String, ForeignKey("rfp_sessions.rfp_id"))

    question_text = Column(Text, nullable=False)
    status = Column(String, default="draft")

    rfp = relationship("RFPSession", back_populates="questions")
    drafts = relationship("Draft", back_populates="question")


# ---------------------------
# DRAFT
# ---------------------------
class Draft(Base):
    __tablename__ = "drafts"

    draft_id = Column(String, primary_key=True)

    rfp_id = Column(String)  # keep if used elsewhere
    question_id = Column(String, ForeignKey("questions.id"))

    answer_text = Column(Text)
    sources_json = Column(JSON)
    retrieval_snapshot = Column(JSON)

    version = Column(Integer, default=1)
    status = Column(String, default="draft")
    edited_by = Column(String)

    question = relationship("Question", back_populates="drafts")