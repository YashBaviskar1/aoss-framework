from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Text, primary_key=True, index=True) # Clerk User ID
    email = Column(Text, unique=True, nullable=False)
    username = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    servers = relationship("Server", back_populates="owner")


class Server(Base):
    __tablename__ = "servers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Text, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    server_tag = Column(Text, nullable=False)
    ip_address = Column(INET, nullable=False)
    hostname = Column(Text, nullable=True)
    
    # Auth fields (simplified for now, usually keys are stored securely/vault)
    ssh_username = Column(Text, nullable=True) 
    ssh_key_path = Column(Text, nullable=True)
    ssh_password_encrypted = Column(Text, nullable=True)
    
    # Dynamic fields
    additional_components = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="servers")
    logs = relationship("ExecutionLog", back_populates="server")


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Text, ForeignKey("users.id"), nullable=False)
    server_id = Column(UUID(as_uuid=True), ForeignKey("servers.id"), nullable=False)
    
    query = Column(Text, nullable=False)
    plan = Column(JSON, nullable=False) # The JSON plan generated
    execution_results = Column(JSON, nullable=True) # The results of execution
    agent_summary = Column(Text, nullable=True) # Natural language summary of results
    
    status = Column(Text, default="Planned") # Planned, Executed, Failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    server = relationship("Server", back_populates="logs")

