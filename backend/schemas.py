from pydantic import BaseModel, IPvAnyAddress
from typing import List, Optional
from uuid import UUID

class ServerCreate(BaseModel):
    serverTag: str
    ipAddress: IPvAnyAddress
    ipAddress: IPvAnyAddress
    hostname: Optional[str] = None
    sshUsername: str = "root" # Default to root if not provided, or make required
    # Security/Auth placeholders
    selectedFileType: Optional[str] = None # 'pem' or 'ppk'
    sshKeyContent: Optional[str] = None # content of the key file
    
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
