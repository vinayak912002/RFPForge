from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class RFPSession(Base):
    __tablename__ = "rfp_sessions"

    rfp_id = Column(String, primary_key=True, index=True)
    client_name = Column(String, nullable=False)
    deadline = Column(DateTime, nullable=False)
    status = Column(String, default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)

    questions = relationship("Question", back_populates="rfp")


class Question(Base):
    __tablename__ = "questions"

    id = Column(String, primary_key=True)
    rfp_id = Column(String, ForeignKey("rfp_sessions.rfp_id"))
    question_text = Column(Text, nullable=False)
    status = Column(String, default="draft")

    rfp = relationship("RFPSession", back_populates="questions")