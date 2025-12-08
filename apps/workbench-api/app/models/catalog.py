"""
Catalog Models
==============
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, BigInteger, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

from app.core.database import Base


class CatalogEntry(Base):
    __tablename__ = "catalog_entries"
    __table_args__ = {"schema": "workbench"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("workbench.tenants.id"))
    connection_id = Column(UUID(as_uuid=True), ForeignKey("workbench.connections.id"))
    entry_type = Column(String(50), nullable=False)
    schema_name = Column(String(255))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    metadata = Column(JSONB, default={})
    columns = Column(JSONB, default=[])
    row_count = Column(BigInteger)
    size_bytes = Column(BigInteger)
    last_scanned_at = Column(DateTime(timezone=True))
    classification = Column(String(50), default="internal")
    tags = Column(ARRAY(Text), default=[])
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class Lineage(Base):
    __tablename__ = "lineage"
    __table_args__ = {"schema": "workbench"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_entry_id = Column(UUID(as_uuid=True), ForeignKey("workbench.catalog_entries.id"))
    target_entry_id = Column(UUID(as_uuid=True), ForeignKey("workbench.catalog_entries.id"))
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("workbench.pipelines.id"))
    transformation_type = Column(String(100))
    column_mappings = Column(JSONB, default=[])
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
