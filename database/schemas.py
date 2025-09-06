from pydantic import BaseModel, Field
from pydantic import BaseModel
from typing import Optional, List, Dict,Any
from datetime import datetime

class LogEntryBase(BaseModel):
    agent_role: str
    status: str
    message: str

class LogEntryCreate(LogEntryBase):
    trace_id: Optional[str] = None
    task_id: Optional[str] = None
    step_id: str = "step-1"
    duration_ms: int = 100
    # payload: Dict = {}
    # rag_context_ids: List[str] = []
    payload: Dict[str,Any] = Field(default_factory=dict)
    rag_context_ids: List[str] = Field(default_factory=list)

class LogEntry(LogEntryBase):
    id: int
    timestamp: datetime
    trace_id: str
    task_id: str
    step_id: str
    duration_ms: int
    payload: Dict[str,Any]
    rag_context_ids: List[str]
    
    class Config:
        from_attributes = True   
        # orm_mode = True
        arbitrary_types_allowed = True 