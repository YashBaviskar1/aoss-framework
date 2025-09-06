# In database/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
from sqlalchemy.orm import Session
from .models import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./logs.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)


Base.metadata.create_all(bind=engine)




SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Generator function that yields database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()