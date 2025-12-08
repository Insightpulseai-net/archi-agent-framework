"""
Notebook Models
===============
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

from app.core.database import Base


class Notebook(Base):
    __tablename__ = "notebooks"
    __table_args__ = {"schema": "workbench"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("workbench.tenants.id"))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    path = Column(String(500))
    content = Column(JSONB, nullable=False, default={"cells": []})
    version = Column(Integer, default=1)
    is_template = Column(Boolean, default=False)
    tags = Column(ARRAY(Text), default=[])
    created_by = Column(UUID(as_uuid=True), ForeignKey("workbench.users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("workbench.users.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class NotebookVersion(Base):
    __tablename__ = "notebook_versions"
    __table_args__ = {"schema": "workbench"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    notebook_id = Column(UUID(as_uuid=True), ForeignKey("workbench.notebooks.id", ondelete="CASCADE"))
    version = Column(Integer, nullable=False)
    content = Column(JSONB, nullable=False)
    change_summary = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("workbench.users.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
