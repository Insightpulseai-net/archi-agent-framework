-- ============================================================================
-- Bronze Layer: Raw Data Ingestion
-- Purpose: Landing zone for raw data from source systems (Odoo, n8n, webhooks)
-- Pattern: Immutable append-only tables with full audit trail
-- ============================================================================

-- Create scout schema for business intelligence data
CREATE SCHEMA IF NOT EXISTS scout;

-- ============================================================================
-- Bronze Tables: Raw Ingestion
-- ============================================================================

-- Bronze Transactions: Raw transaction data from multiple sources
CREATE TABLE IF NOT EXISTS scout.bronze_transactions (
  id               BIGSERIAL PRIMARY KEY,
  tenant_id        UUID        NOT NULL,
  workspace_id     UUID,
  raw_payload      JSONB       NOT NULL DEFAULT '{}'::jsonb,
  source_system    TEXT        NOT NULL,
  source_id        TEXT,
  ingested_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata         JSONB       NOT NULL DEFAULT '{}'::jsonb
);

-- Bronze Expenses: Raw expense data from Odoo
CREATE TABLE IF NOT EXISTS scout.bronze_expenses (
  id               BIGSERIAL PRIMARY KEY,
  tenant_id        UUID        NOT NULL,
  workspace_id     UUID,
  raw_payload      JSONB       NOT NULL DEFAULT '{}'::jsonb,
  source_system    TEXT        NOT NULL,
  source_id        TEXT,
  ingested_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata         JSONB       NOT NULL DEFAULT '{}'::jsonb
);

-- Bronze BIR Forms: Raw BIR tax form data
CREATE TABLE IF NOT EXISTS scout.bronze_bir_forms (
  id               BIGSERIAL PRIMARY KEY,
  tenant_id        UUID        NOT NULL,
  workspace_id     UUID,
  raw_payload      JSONB       NOT NULL DEFAULT '{}'::jsonb,
  source_system    TEXT        NOT NULL,
  source_id        TEXT,
  form_type        TEXT,
  ingested_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata         JSONB       NOT NULL DEFAULT '{}'::jsonb
);

-- Bronze PPM Tasks: Raw project portfolio management task data
CREATE TABLE IF NOT EXISTS scout.bronze_ppm_tasks (
  id               BIGSERIAL PRIMARY KEY,
  tenant_id        UUID        NOT NULL,
  workspace_id     UUID,
  raw_payload      JSONB       NOT NULL DEFAULT '{}'::jsonb,
  source_system    TEXT        NOT NULL,
  source_id        TEXT,
  ingested_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata         JSONB       NOT NULL DEFAULT '{}'::jsonb
);

-- Bronze Agencies: Raw agency/client data
CREATE TABLE IF NOT EXISTS scout.bronze_agencies (
  id               BIGSERIAL PRIMARY KEY,
  tenant_id        UUID        NOT NULL,
  workspace_id     UUID,
  raw_payload      JSONB       NOT NULL DEFAULT '{}'::jsonb,
  source_system    TEXT        NOT NULL,
  source_id        TEXT,
  ingested_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata         JSONB       NOT NULL DEFAULT '{}'::jsonb
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_bronze_transactions_tenant_id
  ON scout.bronze_transactions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_bronze_transactions_source_system
  ON scout.bronze_transactions(source_system);
CREATE INDEX IF NOT EXISTS idx_bronze_transactions_ingested_at
  ON scout.bronze_transactions(ingested_at DESC);

CREATE INDEX IF NOT EXISTS idx_bronze_expenses_tenant_id
  ON scout.bronze_expenses(tenant_id);
CREATE INDEX IF NOT EXISTS idx_bronze_expenses_source_system
  ON scout.bronze_expenses(source_system);
CREATE INDEX IF NOT EXISTS idx_bronze_expenses_ingested_at
  ON scout.bronze_expenses(ingested_at DESC);

CREATE INDEX IF NOT EXISTS idx_bronze_bir_forms_tenant_id
  ON scout.bronze_bir_forms(tenant_id);
CREATE INDEX IF NOT EXISTS idx_bronze_bir_forms_form_type
  ON scout.bronze_bir_forms(form_type);
CREATE INDEX IF NOT EXISTS idx_bronze_bir_forms_ingested_at
  ON scout.bronze_bir_forms(ingested_at DESC);

CREATE INDEX IF NOT EXISTS idx_bronze_ppm_tasks_tenant_id
  ON scout.bronze_ppm_tasks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_bronze_ppm_tasks_source_system
  ON scout.bronze_ppm_tasks(source_system);
CREATE INDEX IF NOT EXISTS idx_bronze_ppm_tasks_ingested_at
  ON scout.bronze_ppm_tasks(ingested_at DESC);

CREATE INDEX IF NOT EXISTS idx_bronze_agencies_tenant_id
  ON scout.bronze_agencies(tenant_id);
CREATE INDEX IF NOT EXISTS idx_bronze_agencies_source_id
  ON scout.bronze_agencies(source_id);

-- ============================================================================
-- Row-Level Security (RLS) Policies
-- ============================================================================

ALTER TABLE scout.bronze_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE scout.bronze_expenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE scout.bronze_bir_forms ENABLE ROW LEVEL SECURITY;
ALTER TABLE scout.bronze_ppm_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE scout.bronze_agencies ENABLE ROW LEVEL SECURITY;

-- Tenant isolation policy for transactions
CREATE POLICY bronze_transactions_tenant_isolation ON scout.bronze_transactions
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Tenant isolation policy for expenses
CREATE POLICY bronze_expenses_tenant_isolation ON scout.bronze_expenses
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Tenant isolation policy for BIR forms
CREATE POLICY bronze_bir_forms_tenant_isolation ON scout.bronze_bir_forms
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Tenant isolation policy for PPM tasks
CREATE POLICY bronze_ppm_tasks_tenant_isolation ON scout.bronze_ppm_tasks
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Tenant isolation policy for agencies
CREATE POLICY bronze_agencies_tenant_isolation ON scout.bronze_agencies
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON SCHEMA scout IS 'Scout business intelligence and analytics data';

COMMENT ON TABLE scout.bronze_transactions IS 'Raw transaction data from source systems - immutable audit trail';
COMMENT ON TABLE scout.bronze_expenses IS 'Raw expense data from Odoo - OCR receipts and manual entries';
COMMENT ON TABLE scout.bronze_bir_forms IS 'Raw BIR tax form data - 1601-C, 2550Q, etc.';
COMMENT ON TABLE scout.bronze_ppm_tasks IS 'Raw PPM task data - project portfolio management';
COMMENT ON TABLE scout.bronze_agencies IS 'Raw agency/client data - brands and entities';

COMMENT ON COLUMN scout.bronze_transactions.raw_payload IS 'Complete JSON payload from source system';
COMMENT ON COLUMN scout.bronze_transactions.source_system IS 'Origin system: odoo, n8n, webhook, manual';
COMMENT ON COLUMN scout.bronze_transactions.metadata IS 'Additional context: user_id, api_version, etc.';
