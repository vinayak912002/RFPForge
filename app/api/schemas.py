from pydantic import BaseModel
from datetime import datetime
from typing import List


class RFPSessionResponse(BaseModel):
    rfp_id: str
    client_name: str
    deadline: datetime
    status: str
    question_count: int


class QuestionResponse(BaseModel):
    id: str
    question_text: str
    status: str


class QuestionListResponse(BaseModel):
    rfp_id: str
    questions: List[QuestionResponse]

class QuestionCreateRequest(BaseModel):
    question_text: str