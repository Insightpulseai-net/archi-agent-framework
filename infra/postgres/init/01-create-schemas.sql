-- ============================================================================
-- Data Engineering Workbench - PostgreSQL Initialization
-- ============================================================================
-- Creates the Medallion architecture schemas and core tables
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- ============================================================================
-- MEDALLION ARCHITECTURE SCHEMAS
-- ============================================================================

-- Bronze Layer: Raw, immutable data as ingested
CREATE SCHEMA IF NOT EXISTS bronze;
COMMENT ON SCHEMA bronze IS 'Raw data layer - immutable, partitioned by date';

-- Silver Layer: Cleaned, validated, deduplicated data
CREATE SCHEMA IF NOT EXISTS silver;
COMMENT ON SCHEMA silver IS 'Cleaned data layer - validated, typed, deduplicated';

-- Gold Layer: Business-ready aggregates and views
CREATE SCHEMA IF NOT EXISTS gold;
COMMENT ON SCHEMA gold IS 'Business layer - aggregates, metrics, ready for consumption';

-- Workbench metadata schema
CREATE SCHEMA IF NOT EXISTS workbench;
COMMENT ON SCHEMA workbench IS 'Workbench application metadata';

-- Audit schema
CREATE SCHEMA IF NOT EXISTS audit;
COMMENT ON SCHEMA audit IS 'Audit logs and compliance data';

-- ============================================================================
-- WORKBENCH CORE TABLES
-- ============================================================================

-- Users
CREATE TABLE IF NOT EXISTS workbench.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'viewer' CHECK (role IN ('viewer', 'developer', 'engineer', 'admin')),
    is_active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON workbench.users(email);
CREATE INDEX idx_users_username ON workbench.users(username);

-- Multi-tenant support (optional)
CREATE TABLE IF NOT EXISTS workbench.tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workbench.tenant_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES workbench.tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES workbench.users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'viewer',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, user_id)
);

-- Connections (data sources)
CREATE TABLE IF NOT EXISTS workbench.connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES workbench.tenants(id),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('postgresql', 'mysql', 'odoo_rpc', 'odoo_rest', 'rest_api', 'sftp', 's3', 'superset', 'ocr_service')),
    config JSONB NOT NULL,
    credentials_encrypted BYTEA,
    is_active BOOLEAN DEFAULT true,
    last_tested_at TIMESTAMP WITH TIME ZONE,
    last_test_status VARCHAR(50),
    created_by UUID REFERENCES workbench.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_connections_tenant ON workbench.connections(tenant_id);
CREATE INDEX idx_connections_type ON workbench.connections(type);

-- Notebooks
CREATE TABLE IF NOT EXISTS workbench.notebooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES workbench.tenants(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    path VARCHAR(500),
    content JSONB NOT NULL DEFAULT '{"cells": []}',
    version INTEGER DEFAULT 1,
    is_template BOOLEAN DEFAULT false,
    tags TEXT[] DEFAULT '{}',
    created_by UUID REFERENCES workbench.users(id),
    updated_by UUID REFERENCES workbench.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_notebooks_tenant ON workbench.notebooks(tenant_id);
CREATE INDEX idx_notebooks_path ON workbench.notebooks(path);
CREATE INDEX idx_notebooks_tags ON workbench.notebooks USING GIN(tags);

-- Notebook versions (for history)
CREATE TABLE IF NOT EXISTS workbench.notebook_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    notebook_id UUID REFERENCES workbench.notebooks(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    content JSONB NOT NULL,
    change_summary TEXT,
    created_by UUID REFERENCES workbench.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(notebook_id, version)
);

-- Pipelines
CREATE TABLE IF NOT EXISTS workbench.pipelines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES workbench.tenants(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    definition JSONB NOT NULL,
    schedule VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    last_run_at TIMESTAMP WITH TIME ZONE,
    last_run_status VARCHAR(50),
    tags TEXT[] DEFAULT '{}',
    created_by UUID REFERENCES workbench.users(id),
    updated_by UUID REFERENCES workbench.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_pipelines_tenant ON workbench.pipelines(tenant_id);
CREATE INDEX idx_pipelines_schedule ON workbench.pipelines(schedule) WHERE schedule IS NOT NULL;

-- Pipeline runs
CREATE TABLE IF NOT EXISTS workbench.pipeline_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pipeline_id UUID REFERENCES workbench.pipelines(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    trigger_type VARCHAR(50) DEFAULT 'manual' CHECK (trigger_type IN ('manual', 'scheduled', 'webhook', 'event')),
    parameters JSONB DEFAULT '{}',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    error_message TEXT,
    logs JSONB DEFAULT '[]',
    metrics JSONB DEFAULT '{}',
    triggered_by UUID REFERENCES workbench.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_pipeline_runs_pipeline ON workbench.pipeline_runs(pipeline_id);
CREATE INDEX idx_pipeline_runs_status ON workbench.pipeline_runs(status);
CREATE INDEX idx_pipeline_runs_created ON workbench.pipeline_runs(created_at DESC);

-- Pipeline tasks (individual steps in a run)
CREATE TABLE IF NOT EXISTS workbench.pipeline_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID REFERENCES workbench.pipeline_runs(id) ON DELETE CASCADE,
    task_name VARCHAR(255) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    config JSONB DEFAULT '{}',
    output JSONB,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_pipeline_tasks_run ON workbench.pipeline_tasks(run_id);

-- ============================================================================
-- DATA CATALOG TABLES
-- ============================================================================

-- Catalog entries (tables, views, files)
CREATE TABLE IF NOT EXISTS workbench.catalog_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES workbench.tenants(id),
    connection_id UUID REFERENCES workbench.connections(id),
    entry_type VARCHAR(50) NOT NULL CHECK (entry_type IN ('table', 'view', 'file', 'api_endpoint')),
    schema_name VARCHAR(255),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    columns JSONB DEFAULT '[]',
    row_count BIGINT,
    size_bytes BIGINT,
    last_scanned_at TIMESTAMP WITH TIME ZONE,
    classification VARCHAR(50) DEFAULT 'internal' CHECK (classification IN ('public', 'internal', 'confidential', 'restricted')),
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_catalog_tenant ON workbench.catalog_entries(tenant_id);
CREATE INDEX idx_catalog_connection ON workbench.catalog_entries(connection_id);
CREATE INDEX idx_catalog_name ON workbench.catalog_entries(name);
CREATE INDEX idx_catalog_tags ON workbench.catalog_entries USING GIN(tags);

-- Full-text search index
CREATE INDEX idx_catalog_search ON workbench.catalog_entries
USING GIN(to_tsvector('english', coalesce(name, '') || ' ' || coalesce(description, '')));

-- Data lineage
CREATE TABLE IF NOT EXISTS workbench.lineage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_entry_id UUID REFERENCES workbench.catalog_entries(id),
    target_entry_id UUID REFERENCES workbench.catalog_entries(id),
    pipeline_id UUID REFERENCES workbench.pipelines(id),
    transformation_type VARCHAR(100),
    column_mappings JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_lineage_source ON workbench.lineage(source_entry_id);
CREATE INDEX idx_lineage_target ON workbench.lineage(target_entry_id);

-- ============================================================================
-- AUDIT TABLES
-- ============================================================================

-- General audit log
CREATE TABLE IF NOT EXISTS audit.activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID,
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_tenant ON audit.activity_log(tenant_id);
CREATE INDEX idx_audit_user ON audit.activity_log(user_id);
CREATE INDEX idx_audit_action ON audit.activity_log(action);
CREATE INDEX idx_audit_created ON audit.activity_log(created_at DESC);

-- Data access log (for compliance)
CREATE TABLE IF NOT EXISTS audit.data_access_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID,
    user_id UUID,
    catalog_entry_id UUID,
    access_type VARCHAR(50) NOT NULL CHECK (access_type IN ('read', 'write', 'delete', 'export')),
    query_hash VARCHAR(64),
    rows_accessed INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_data_access_tenant ON audit.data_access_log(tenant_id);
CREATE INDEX idx_data_access_entry ON audit.data_access_log(catalog_entry_id);
CREATE INDEX idx_data_access_created ON audit.data_access_log(created_at DESC);

-- ============================================================================
-- BRONZE LAYER TABLES (Example structures)
-- ============================================================================

-- Raw document extractions
CREATE TABLE IF NOT EXISTS bronze.documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID,
    storage_url TEXT NOT NULL,
    file_name VARCHAR(500),
    mime_type VARCHAR(100),
    file_size_bytes BIGINT,
    checksum VARCHAR(64),
    source VARCHAR(100),
    raw_metadata JSONB DEFAULT '{}',
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_doc_checksum UNIQUE(tenant_id, checksum)
);

CREATE INDEX idx_bronze_docs_tenant ON bronze.documents(tenant_id);
CREATE INDEX idx_bronze_docs_ingested ON bronze.documents(ingested_at DESC);

-- Raw OCR extractions
CREATE TABLE IF NOT EXISTS bronze.ocr_extractions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES bronze.documents(id),
    ocr_engine VARCHAR(50),
    ocr_version VARCHAR(50),
    raw_text TEXT,
    raw_regions JSONB,
    confidence_score DECIMAL(5,4),
    processing_time_ms INTEGER,
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_bronze_ocr_doc ON bronze.ocr_extractions(document_id);

-- Raw Odoo data extracts
CREATE TABLE IF NOT EXISTS bronze.odoo_extracts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID,
    model_name VARCHAR(255) NOT NULL,
    record_id INTEGER NOT NULL,
    raw_data JSONB NOT NULL,
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    extract_batch_id UUID,
    CONSTRAINT unique_odoo_record UNIQUE(tenant_id, model_name, record_id, extract_batch_id)
);

CREATE INDEX idx_bronze_odoo_tenant ON bronze.odoo_extracts(tenant_id);
CREATE INDEX idx_bronze_odoo_model ON bronze.odoo_extracts(model_name);
CREATE INDEX idx_bronze_odoo_batch ON bronze.odoo_extracts(extract_batch_id);

-- ============================================================================
-- SILVER LAYER TABLES (Example structures)
-- ============================================================================

-- Standardized invoices
CREATE TABLE IF NOT EXISTS silver.invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID,
    source_document_id UUID REFERENCES bronze.documents(id),
    source_type VARCHAR(50),
    invoice_number VARCHAR(100),
    invoice_date DATE,
    due_date DATE,
    vendor_id UUID,
    vendor_name VARCHAR(255),
    vendor_tax_id VARCHAR(50),
    currency CHAR(3) DEFAULT 'USD',
    subtotal DECIMAL(18,2),
    tax_amount DECIMAL(18,2),
    total_amount DECIMAL(18,2),
    line_items JSONB DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'draft',
    validation_flags JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_silver_inv_tenant ON silver.invoices(tenant_id);
CREATE INDEX idx_silver_inv_vendor ON silver.invoices(vendor_id);
CREATE INDEX idx_silver_inv_date ON silver.invoices(invoice_date);

-- Standardized GL transactions
CREATE TABLE IF NOT EXISTS silver.gl_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID,
    source_record_id INTEGER,
    journal_entry_id UUID,
    account_code VARCHAR(50),
    account_name VARCHAR(255),
    debit DECIMAL(18,2) DEFAULT 0,
    credit DECIMAL(18,2) DEFAULT 0,
    currency CHAR(3) DEFAULT 'USD',
    posting_date DATE NOT NULL,
    period_id VARCHAR(20),
    description TEXT,
    partner_id UUID,
    partner_name VARCHAR(255),
    reconciled BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_silver_gl_tenant ON silver.gl_transactions(tenant_id);
CREATE INDEX idx_silver_gl_date ON silver.gl_transactions(posting_date);
CREATE INDEX idx_silver_gl_account ON silver.gl_transactions(account_code);
CREATE INDEX idx_silver_gl_period ON silver.gl_transactions(period_id);

-- ============================================================================
-- GOLD LAYER TABLES (Example structures)
-- ============================================================================

-- AP Aging Summary
CREATE TABLE IF NOT EXISTS gold.ap_aging (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID,
    as_of_date DATE NOT NULL,
    vendor_id UUID,
    vendor_name VARCHAR(255),
    current_amount DECIMAL(18,2) DEFAULT 0,
    days_1_30 DECIMAL(18,2) DEFAULT 0,
    days_31_60 DECIMAL(18,2) DEFAULT 0,
    days_61_90 DECIMAL(18,2) DEFAULT 0,
    days_over_90 DECIMAL(18,2) DEFAULT 0,
    total_outstanding DECIMAL(18,2) DEFAULT 0,
    currency CHAR(3) DEFAULT 'USD',
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_gold_ap_tenant ON gold.ap_aging(tenant_id);
CREATE INDEX idx_gold_ap_date ON gold.ap_aging(as_of_date);

-- Trial Balance
CREATE TABLE IF NOT EXISTS gold.trial_balance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID,
    period_id VARCHAR(20) NOT NULL,
    account_code VARCHAR(50) NOT NULL,
    account_name VARCHAR(255),
    account_type VARCHAR(50),
    opening_debit DECIMAL(18,2) DEFAULT 0,
    opening_credit DECIMAL(18,2) DEFAULT 0,
    period_debit DECIMAL(18,2) DEFAULT 0,
    period_credit DECIMAL(18,2) DEFAULT 0,
    closing_debit DECIMAL(18,2) DEFAULT 0,
    closing_credit DECIMAL(18,2) DEFAULT 0,
    currency CHAR(3) DEFAULT 'USD',
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_tb_entry UNIQUE(tenant_id, period_id, account_code)
);

CREATE INDEX idx_gold_tb_tenant ON gold.trial_balance(tenant_id);
CREATE INDEX idx_gold_tb_period ON gold.trial_balance(period_id);

-- ============================================================================
-- ROW LEVEL SECURITY (for multi-tenant)
-- ============================================================================

-- Enable RLS on tenant-scoped tables
ALTER TABLE workbench.connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE workbench.notebooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE workbench.pipelines ENABLE ROW LEVEL SECURITY;
ALTER TABLE workbench.pipeline_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE workbench.catalog_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE bronze.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE bronze.odoo_extracts ENABLE ROW LEVEL SECURITY;
ALTER TABLE silver.invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE silver.gl_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE gold.ap_aging ENABLE ROW LEVEL SECURITY;
ALTER TABLE gold.trial_balance ENABLE ROW LEVEL SECURITY;

-- Note: Actual RLS policies should be created based on your auth implementation
-- Example policy (uncomment and modify as needed):
-- CREATE POLICY tenant_isolation ON workbench.notebooks
--     USING (tenant_id = current_setting('app.tenant_id')::uuid);

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON workbench.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_connections_updated_at BEFORE UPDATE ON workbench.connections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_notebooks_updated_at BEFORE UPDATE ON workbench.notebooks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_pipelines_updated_at BEFORE UPDATE ON workbench.pipelines
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_catalog_updated_at BEFORE UPDATE ON workbench.catalog_entries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================================
-- SEED DATA
-- ============================================================================

-- Insert default tenant
INSERT INTO workbench.tenants (slug, name, settings)
VALUES ('default', 'Default Tenant', '{"features": {"multi_user": true}}')
ON CONFLICT (slug) DO NOTHING;

-- Insert default admin user (password: change_me_immediately)
-- Password hash for 'change_me_immediately' using bcrypt
INSERT INTO workbench.users (email, username, password_hash, full_name, role)
VALUES (
    'admin@insightpulseai.net',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.S/3.R0Q/6/2w.e',
    'System Administrator',
    'admin'
)
ON CONFLICT (email) DO NOTHING;

COMMIT;
