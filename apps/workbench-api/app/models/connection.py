"""
Connection Model
================
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Boolean, DateTime, LargeBinary, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class Connection(Base):
    __tablename__ = "connections"
    __table_args__ = {"schema": "workbench"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("workbench.tenants.id"))
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    config = Column(JSONB, nullable=False)
    credentials_encrypted = Column(LargeBinary)
    is_active = Column(Boolean, default=True)
    last_tested_at = Column(DateTime(timezone=True))
    last_test_status = Column(String(50))
    created_by = Column(UUID(as_uuid=True), ForeignKey("workbench.users.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
