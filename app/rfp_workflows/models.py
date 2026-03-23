import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base


class RFPSession(Base):
    __tablename__ = "rfp_sessions"

    rfp_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_name = Column(String, nullable=False)
    deadline = Column(DateTime, nullable=False)
    status = Column(String, default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)

    questions = relationship("Question", back_populates="rfp")


class Question(Base):
    __tablename__ = "questions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    rfp_id = Column(String, ForeignKey("rfp_sessions.rfp_id"))

    question_text = Column(Text, nullable=False)
    status = Column(String, default="draft")

    rfp = relationship("RFPSession", back_populates="questions")
    drafts = relationship("Draft", back_populates="question")


class Draft(Base):
    __tablename__ = "drafts"

    draft_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id = Column(String, ForeignKey("questions.id"))

    answer_text = Column(Text)
    sources_json = Column(JSON)
    version = Column(Integer)
    edited_by = Column(String)

    question = relationship("Question", back_populates="drafts")