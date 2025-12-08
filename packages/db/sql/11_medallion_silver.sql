-- ============================================================================
-- Silver Layer: Validated & Cleaned Data
-- Purpose: Typed, validated, business-rule compliant data
-- Pattern: Derived from Bronze with data quality checks
-- ============================================================================

-- ============================================================================
-- Silver Tables: Validated Business Entities
-- ============================================================================

-- Silver Transactions: Validated transaction data with proper types
CREATE TABLE IF NOT EXISTS scout.silver_transactions (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID        NOT NULL,
  workspace_id      UUID,
  bronze_id         BIGINT      NOT NULL REFERENCES scout.bronze_transactions(id),

  -- Business fields
  transaction_date  TIMESTAMPTZ NOT NULL,
  amount            NUMERIC(15,2) NOT NULL,
  currency          TEXT        NOT NULL DEFAULT 'PHP',
  description       TEXT,
  category          TEXT,
  vendor_name       TEXT,

  -- Status tracking
  status            TEXT        NOT NULL DEFAULT 'pending',
  validation_errors JSONB       DEFAULT '[]'::jsonb,
  quality_score     NUMERIC(3,2),

  -- Audit fields
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata          JSONB       NOT NULL DEFAULT '{}'::jsonb
);

-- Silver Expenses: Validated expense records with OCR confidence
CREATE TABLE IF NOT EXISTS scout.silver_expenses (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID        NOT NULL,
  workspace_id      UUID,
  bronze_id         BIGINT      NOT NULL REFERENCES scout.bronze_expenses(id),

  -- Business fields
  expense_date      TIMESTAMPTZ NOT NULL,
  amount            NUMERIC(15,2) NOT NULL,
  currency          TEXT        NOT NULL DEFAULT 'PHP',
  category          TEXT        NOT NULL,
  vendor_name       TEXT,
  description       TEXT,

  -- OCR-specific fields
  ocr_confidence    NUMERIC(3,2),
  ocr_provider      TEXT,
  receipt_url       TEXT,

  -- BIR compliance fields
  tin               TEXT,
  tax_type          TEXT,
  withholding_tax   NUMERIC(15,2),

  -- Status tracking
  status            TEXT        NOT NULL DEFAULT 'draft',
  validation_errors JSONB       DEFAULT '[]'::jsonb,
  quality_score     NUMERIC(3,2),

  -- Audit fields
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata          JSONB       NOT NULL DEFAULT '{}'::jsonb
);

-- Silver BIR Forms: Validated tax form data
CREATE TABLE IF NOT EXISTS scout.silver_bir_forms (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID        NOT NULL,
  workspace_id      UUID,
  bronze_id         BIGINT      NOT NULL REFERENCES scout.bronze_bir_forms(id),

  -- Business fields
  form_type         TEXT        NOT NULL,
  filing_period     TEXT        NOT NULL,
  filing_deadline   TIMESTAMPTZ NOT NULL,

  -- Tax computation fields
  gross_income      NUMERIC(15,2),
  withholding_tax   NUMERIC(15,2),
  net_tax_due       NUMERIC(15,2),

  -- Agency tracking
  agency_name       TEXT,
  agency_tin        TEXT,
  employee_name     TEXT,

  -- Status tracking
  status            TEXT        NOT NULL DEFAULT 'draft',
  filed_date        TIMESTAMPTZ,
  validation_errors JSONB       DEFAULT '[]'::jsonb,
  quality_score     NUMERIC(3,2),

  -- Audit fields
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata          JSONB       NOT NULL DEFAULT '{}'::jsonb
);

-- Silver PPM Tasks: Validated project tasks with logframe linkage
CREATE TABLE IF NOT EXISTS scout.silver_ppm_tasks (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID        NOT NULL,
  workspace_id      UUID,
  bronze_id         BIGINT      NOT NULL REFERENCES scout.bronze_ppm_tasks(id),

  -- Business fields
  task_name         TEXT        NOT NULL,
  task_type         TEXT        NOT NULL,
  priority          TEXT        NOT NULL DEFAULT 'medium',
  due_date          TIMESTAMPTZ,
  completion_date   TIMESTAMPTZ,

  -- Logframe tracking
  logframe_level    TEXT,
  logframe_id       UUID,

  -- Responsibility
  assigned_to       TEXT,
  responsible_role  TEXT,

  -- Status tracking
  status            TEXT        NOT NULL DEFAULT 'not_started',
  progress_pct      NUMERIC(5,2) DEFAULT 0.00,
  validation_errors JSONB       DEFAULT '[]'::jsonb,
  quality_score     NUMERIC(3,2),

  -- Audit fields
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata          JSONB       NOT NULL DEFAULT '{}'::jsonb
);

-- Silver Agencies: Validated agency/client master data
CREATE TABLE IF NOT EXISTS scout.silver_agencies (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID        NOT NULL,
  workspace_id      UUID,
  bronze_id         BIGINT      NOT NULL REFERENCES scout.bronze_agencies(id),

  -- Business fields
  agency_code       TEXT        NOT NULL,
  agency_name       TEXT        NOT NULL,
  tin               TEXT,
  address           TEXT,

  -- Financial tracking
  currency          TEXT        NOT NULL DEFAULT 'PHP',
  payment_terms     TEXT,
  credit_limit      NUMERIC(15,2),

  -- Relationship tracking
  account_manager   TEXT,
  finance_director  TEXT,

  -- Status tracking
  status            TEXT        NOT NULL DEFAULT 'active',
  validation_errors JSONB       DEFAULT '[]'::jsonb,
  quality_score     NUMERIC(3,2),

  -- Audit fields
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata          JSONB       NOT NULL DEFAULT '{}'::jsonb
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_silver_transactions_tenant_id
  ON scout.silver_transactions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_silver_transactions_date
  ON scout.silver_transactions(transaction_date DESC);
CREATE INDEX IF NOT EXISTS idx_silver_transactions_status
  ON scout.silver_transactions(status);

CREATE INDEX IF NOT EXISTS idx_silver_expenses_tenant_id
  ON scout.silver_expenses(tenant_id);
CREATE INDEX IF NOT EXISTS idx_silver_expenses_date
  ON scout.silver_expenses(expense_date DESC);
CREATE INDEX IF NOT EXISTS idx_silver_expenses_category
  ON scout.silver_expenses(category);
CREATE INDEX IF NOT EXISTS idx_silver_expenses_status
  ON scout.silver_expenses(status);

CREATE INDEX IF NOT EXISTS idx_silver_bir_forms_tenant_id
  ON scout.silver_bir_forms(tenant_id);
CREATE INDEX IF NOT EXISTS idx_silver_bir_forms_type_period
  ON scout.silver_bir_forms(form_type, filing_period);
CREATE INDEX IF NOT EXISTS idx_silver_bir_forms_deadline
  ON scout.silver_bir_forms(filing_deadline);

CREATE INDEX IF NOT EXISTS idx_silver_ppm_tasks_tenant_id
  ON scout.silver_ppm_tasks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_silver_ppm_tasks_status
  ON scout.silver_ppm_tasks(status);
CREATE INDEX IF NOT EXISTS idx_silver_ppm_tasks_due_date
  ON scout.silver_ppm_tasks(due_date);

CREATE INDEX IF NOT EXISTS idx_silver_agencies_tenant_id
  ON scout.silver_agencies(tenant_id);
CREATE INDEX IF NOT EXISTS idx_silver_agencies_code
  ON scout.silver_agencies(agency_code);
CREATE INDEX IF NOT EXISTS idx_silver_agencies_status
  ON scout.silver_agencies(status);

-- ============================================================================
-- Row-Level Security (RLS) Policies
-- ============================================================================

ALTER TABLE scout.silver_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE scout.silver_expenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE scout.silver_bir_forms ENABLE ROW LEVEL SECURITY;
ALTER TABLE scout.silver_ppm_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE scout.silver_agencies ENABLE ROW LEVEL SECURITY;

CREATE POLICY silver_transactions_tenant_isolation ON scout.silver_transactions
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY silver_expenses_tenant_isolation ON scout.silver_expenses
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY silver_bir_forms_tenant_isolation ON scout.silver_bir_forms
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY silver_ppm_tasks_tenant_isolation ON scout.silver_ppm_tasks
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY silver_agencies_tenant_isolation ON scout.silver_agencies
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- ============================================================================
-- Triggers for Automatic Timestamps
-- ============================================================================

CREATE OR REPLACE FUNCTION scout.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_silver_transactions_updated_at
  BEFORE UPDATE ON scout.silver_transactions
  FOR EACH ROW EXECUTE FUNCTION scout.update_updated_at_column();

CREATE TRIGGER update_silver_expenses_updated_at
  BEFORE UPDATE ON scout.silver_expenses
  FOR EACH ROW EXECUTE FUNCTION scout.update_updated_at_column();

CREATE TRIGGER update_silver_bir_forms_updated_at
  BEFORE UPDATE ON scout.silver_bir_forms
  FOR EACH ROW EXECUTE FUNCTION scout.update_updated_at_column();

CREATE TRIGGER update_silver_ppm_tasks_updated_at
  BEFORE UPDATE ON scout.silver_ppm_tasks
  FOR EACH ROW EXECUTE FUNCTION scout.update_updated_at_column();

CREATE TRIGGER update_silver_agencies_updated_at
  BEFORE UPDATE ON scout.silver_agencies
  FOR EACH ROW EXECUTE FUNCTION scout.update_updated_at_column();

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE scout.silver_transactions IS 'Validated transaction data with proper types and business rules';
COMMENT ON TABLE scout.silver_expenses IS 'Validated expense records with OCR confidence and BIR compliance';
COMMENT ON TABLE scout.silver_bir_forms IS 'Validated tax form data ready for filing';
COMMENT ON TABLE scout.silver_ppm_tasks IS 'Validated project tasks with logframe linkage';
COMMENT ON TABLE scout.silver_agencies IS 'Validated agency/client master data';

COMMENT ON COLUMN scout.silver_expenses.ocr_confidence IS 'OCR extraction confidence score 0.00-1.00';
COMMENT ON COLUMN scout.silver_expenses.quality_score IS 'Data quality score 0.00-1.00 based on validation rules';
COMMENT ON COLUMN scout.silver_bir_forms.filing_deadline IS 'Official BIR filing deadline from BIR_SCHEDULE_2026.xlsx';
