# DB operations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base

from docx import Document
from pypdf import PdfReader

DATABASE_URL = "sqlite:///./rfp.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)




def extract_questions(text: str):
    lines = text.split("\n")
    questions = []

    for line in lines:
        line = line.strip()
        if line.endswith("?") and len(line) > 15:
            questions.append(line)

    return questions


def parse_file(file):
    filename = file.filename

    if filename.endswith(".pdf"):
        reader = PdfReader(file.file)
        text = ""
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text()
        return extract_questions(text)

    elif filename.endswith(".docx"):
        doc = Document(file.file)
        text = "\n".join([p.text for p in doc.paragraphs])
        return extract_questions(text)

    return []