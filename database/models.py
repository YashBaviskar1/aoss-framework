from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class LogEntry(Base):
    __tablename__ = "log_entries"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    trace_id = Column(String(36), index=True)
    task_id = Column(String(36), index=True)
    step_id = Column(String(50), default="step-1")
    agent_role = Column(String(50), index=True)
    status = Column(String(20))
    duration_ms = Column(Integer, default=100)
    message = Column(String(500))
    payload = Column(JSON)
    rag_context_ids = Column(JSON)  # Stored as JSON array