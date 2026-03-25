from pydantic import BaseModel
from datetime import datetime
from typing import List


# ------------------ CREATE REQUEST ------------------

class RFPSessionCreateRequest(BaseModel):
    client_name: str
    deadline: datetime


class QuestionCreateRequest(BaseModel):
    rfp_id: str
    question_text: str


class DraftCreateRequest(BaseModel):
    question_id: str
    answer_text: str
    version: int


# ------------------ RESPONSE ------------------

class RFPSessionResponse(BaseModel):
    rfp_id: str
    client_name: str
    deadline: datetime

    class Config:
        from_attributes = True


class QuestionResponse(BaseModel):
    question_id: str
    rfp_id: str
    question_text: str

    class Config:
        from_attributes = True


class DraftResponse(BaseModel):
    draft_id: str
    question_id: str
    answer_text: str
    version: int

    class Config:
        from_attributes = True


# ------------------ LIST ------------------

class QuestionListResponse(BaseModel):
    questions: List[QuestionResponse]


class DraftListResponse(BaseModel):
    drafts: List[DraftResponse]