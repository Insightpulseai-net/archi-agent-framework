"""
Pipeline Models
===============
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

from app.core.database import Base


class Pipeline(Base):
    __tablename__ = "pipelines"
    __table_args__ = {"schema": "workbench"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("workbench.tenants.id"))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    definition = Column(JSONB, nullable=False)
    schedule = Column(String(100))
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime(timezone=True))
    last_run_status = Column(String(50))
    tags = Column(ARRAY(Text), default=[])
    created_by = Column(UUID(as_uuid=True), ForeignKey("workbench.users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("workbench.users.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"
    __table_args__ = {"schema": "workbench"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("workbench.pipelines.id", ondelete="CASCADE"))
    status = Column(String(50), nullable=False, default="pending")
    trigger_type = Column(String(50), default="manual")
    parameters = Column(JSONB, default={})
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_ms = Column(Integer)
    error_message = Column(Text)
    logs = Column(JSONB, default=[])
    metrics = Column(JSONB, default={})
    triggered_by = Column(UUID(as_uuid=True), ForeignKey("workbench.users.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class PipelineTask(Base):
    __tablename__ = "pipeline_tasks"
    __table_args__ = {"schema": "workbench"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("workbench.pipeline_runs.id", ondelete="CASCADE"))
    task_name = Column(String(255), nullable=False)
    task_type = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    config = Column(JSONB, default={})
    output = Column(JSONB)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_ms = Column(Integer)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
