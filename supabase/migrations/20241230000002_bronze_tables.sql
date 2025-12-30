-- Migration: 20241230000002_bronze_tables.sql
-- Description: Create bronze layer tables for raw data ingestion
-- Author: InsightPulseAI

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- Bronze Layer: Raw Webhook Logs
-- =====================================================

CREATE TABLE bronze.webhook_log (
    id BIGSERIAL PRIMARY KEY,
    event_id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    source VARCHAR(50) NOT NULL DEFAULT 'odoo',
    model_name VARCHAR(255) NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('create', 'write', 'unlink')),
    record_id BIGINT,
    payload JSONB NOT NULL,
    headers JSONB,
    signature VARCHAR(512),
    signature_valid BOOLEAN DEFAULT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at TIMESTAMPTZ,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for webhook_log
CREATE INDEX idx_bronze_webhook_model ON bronze.webhook_log(model_name);
CREATE INDEX idx_bronze_webhook_action ON bronze.webhook_log(action);
CREATE INDEX idx_bronze_webhook_processed ON bronze.webhook_log(processed_at) WHERE processed_at IS NULL;
CREATE INDEX idx_bronze_webhook_received ON bronze.webhook_log(received_at);

COMMENT ON TABLE bronze.webhook_log IS 'Raw webhook payloads from Odoo and other sources';

-- =====================================================
-- Bronze Layer: Odoo Model Sync Logs
-- =====================================================

CREATE TABLE bronze.odoo_sync_log (
    id BIGSERIAL PRIMARY KEY,
    sync_id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    model_name VARCHAR(255) NOT NULL,
    sync_type VARCHAR(20) NOT NULL CHECK (sync_type IN ('full', 'incremental', 'delta')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    records_fetched INTEGER DEFAULT 0,
    records_created INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    last_write_date TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    error_log JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_bronze_sync_model ON bronze.odoo_sync_log(model_name);
CREATE INDEX idx_bronze_sync_status ON bronze.odoo_sync_log(status);

COMMENT ON TABLE bronze.odoo_sync_log IS 'Batch sync operation logs from Odoo';

-- =====================================================
-- Bronze Layer: File Imports
-- =====================================================

CREATE TABLE bronze.file_import (
    id BIGSERIAL PRIMARY KEY,
    import_id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    file_name VARCHAR(512) NOT NULL,
    file_path VARCHAR(1024),
    file_type VARCHAR(50) NOT NULL,
    file_size_bytes BIGINT,
    storage_bucket VARCHAR(255) DEFAULT 'imports',
    storage_key VARCHAR(1024),
    content_hash VARCHAR(64),
    uploaded_by UUID REFERENCES auth.users(id),
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at TIMESTAMPTZ,
    records_extracted INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_bronze_import_status ON bronze.file_import(status);
CREATE INDEX idx_bronze_import_type ON bronze.file_import(file_type);

COMMENT ON TABLE bronze.file_import IS 'File import tracking (CSV, Excel, PDF, etc.)';

-- =====================================================
-- Bronze Layer: Raw Odoo Records (JSON Storage)
-- =====================================================

CREATE TABLE bronze.odoo_records (
    id BIGSERIAL PRIMARY KEY,
    record_id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    odoo_model VARCHAR(255) NOT NULL,
    odoo_id BIGINT NOT NULL,
    odoo_data JSONB NOT NULL,
    write_date TIMESTAMPTZ,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_sync_id UUID REFERENCES bronze.odoo_sync_log(sync_id),
    UNIQUE(odoo_model, odoo_id)
);

CREATE INDEX idx_bronze_records_model ON bronze.odoo_records(odoo_model);
CREATE INDEX idx_bronze_records_odoo_id ON bronze.odoo_records(odoo_id);
CREATE INDEX idx_bronze_records_write_date ON bronze.odoo_records(write_date);

COMMENT ON TABLE bronze.odoo_records IS 'Raw Odoo record snapshots in JSON format';
