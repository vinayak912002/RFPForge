from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from app.db.base import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./rfp.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)