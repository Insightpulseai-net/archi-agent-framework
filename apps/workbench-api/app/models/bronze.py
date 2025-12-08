"""
Bronze Layer Models
===================
Raw data layer for the Medallion architecture.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Text, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class Document(Base):
    """Raw document storage."""
    __tablename__ = "documents"
    __table_args__ = {"schema": "bronze"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True))
    storage_url = Column(Text, nullable=False)
    file_name = Column(String(500))
    mime_type = Column(String(100))
    file_size_bytes = Column(BigInteger)
    checksum = Column(String(64))
    source = Column(String(100))
    raw_metadata = Column(JSONB, default={})
    ingested_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class OCRExtraction(Base):
    """Raw OCR extraction results."""
    __tablename__ = "ocr_extractions"
    __table_args__ = {"schema": "bronze"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("bronze.documents.id"))
    ocr_engine = Column(String(50))
    ocr_version = Column(String(50))
    raw_text = Column(Text)
    raw_regions = Column(JSONB)
    confidence_score = Column(Numeric(5, 4))
    processing_time_ms = Column(Integer)
    extracted_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class OdooExtract(Base):
    """Raw Odoo data extracts."""
    __tablename__ = "odoo_extracts"
    __table_args__ = {"schema": "bronze"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True))
    model_name = Column(String(255), nullable=False)
    record_id = Column(Integer, nullable=False)
    raw_data = Column(JSONB, nullable=False)
    extracted_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    extract_batch_id = Column(UUID(as_uuid=True))
