from pydantic import BaseModel, IPvAnyAddress
from typing import Optional, List, Any, Dict
from uuid import UUID
from datetime import datetime

class ServerCreate(BaseModel):
    id: Optional[int] = None # Frontend React key, ignored by backend
    serverTag: str
    ipAddress: IPvAnyAddress
    hostname: Optional[str] = None
    sshUsername: str = "root" # Default to root if not provided, or make required
    # Security/Auth placeholders
    selectedFileType: Optional[str] = None # 'pem' or 'ppk'
    sshKeyContent: Optional[str] = None # content of the key file
    pemFile: Optional[Any] = None # Ignored, handled via sshKeyContent
    ppkFile: Optional[Any] = None # Ignored, handled via sshKeyContent
    serverPassword: Optional[str] = None # For future password-based auth
    
    class Config:
        from_attributes = True

class ProfileSubmit(BaseModel):
    userId: str
    email: str
    userName: str
    servers: List[ServerCreate]

class UserStatus(BaseModel):
    exists: bool
    username: Optional[str] = None

class ServerResponse(BaseModel):
    id: UUID
    server_tag: str
    ip_address: str
    hostname: Optional[str]
    # status: str = "Online" # Mock status for dashboard
    
    class Config:
        from_attributes = True

class DashboardData(BaseModel):
    user_name: str
    servers: List[ServerResponse]

# --- Orchestration Schemas ---

class PlanStep(BaseModel):
    step: int
    command: str
    description: Optional[str] = None
    status: Optional[str] = None # For logs
    stdout: Optional[str] = None
    stderr: Optional[str] = None

class PlanRequest(BaseModel):
    serverId: str
    query: str
    # NEW FIELDS
    model: str = "llama-3.3-70b-versatile" 
    agent_type: str = "general"

class PlanResponse(BaseModel):
    plan: List[PlanStep]

class ExecuteRequest(BaseModel):
    serverId: str
    plan: List[PlanStep]
    query: str # Original query for logging

class ExecutionLogResponse(BaseModel):
    id: UUID
    query: str
    plan: List[PlanStep]
    status: str
    execution_results: Optional[List[Dict[str, Any]]] = None
    agent_summary: Optional[str] = None # NEW FIELD
    created_at: datetime
    
    class Config:
        from_attributes = True

class ExecutionHistory(BaseModel):
    logs: List[ExecutionLogResponse]

class MonitoringRequest(BaseModel):
    aws_access_key: str
    aws_secret_key: str
    aws_region: str
    instance_id: str
