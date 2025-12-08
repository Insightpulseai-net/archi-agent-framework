-- ============================================================================
-- Gold Layer: Analytics & Business Intelligence
-- Purpose: Pre-aggregated views, KPIs, and analytics-ready datasets
-- Pattern: Optimized for querying and reporting (Apache Superset, Tableau)
-- ============================================================================

-- ============================================================================
-- Gold Views: Expense Analytics
-- ============================================================================

-- Expense Summary by Category and Month
CREATE OR REPLACE VIEW scout.gold_expense_summary AS
SELECT
  e.tenant_id,
  e.workspace_id,
  DATE_TRUNC('month', e.expense_date) AS month,
  e.category,
  e.currency,
  COUNT(*) AS expense_count,
  SUM(e.amount) AS total_amount,
  AVG(e.amount) AS avg_amount,
  MIN(e.amount) AS min_amount,
  MAX(e.amount) AS max_amount,
  AVG(e.ocr_confidence) AS avg_ocr_confidence,
  SUM(e.withholding_tax) AS total_withholding_tax,
  COUNT(*) FILTER (WHERE e.status = 'approved') AS approved_count,
  COUNT(*) FILTER (WHERE e.status = 'pending') AS pending_count,
  COUNT(*) FILTER (WHERE e.status = 'rejected') AS rejected_count
FROM scout.silver_expenses e
GROUP BY e.tenant_id, e.workspace_id, DATE_TRUNC('month', e.expense_date), e.category, e.currency;

-- Expense Trend Analysis (Daily)
CREATE OR REPLACE VIEW scout.gold_expense_trend AS
SELECT
  e.tenant_id,
  DATE_TRUNC('day', e.expense_date) AS day,
  COUNT(*) AS expense_count,
  SUM(e.amount) AS total_amount,
  AVG(e.ocr_confidence) AS avg_ocr_confidence,
  COUNT(*) FILTER (WHERE e.quality_score >= 0.80) AS high_quality_count,
  COUNT(*) FILTER (WHERE e.quality_score < 0.80) AS low_quality_count
FROM scout.silver_expenses e
WHERE e.expense_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY e.tenant_id, DATE_TRUNC('day', e.expense_date);

-- Top Vendors by Expense Volume
CREATE OR REPLACE VIEW scout.gold_top_vendors AS
SELECT
  e.tenant_id,
  e.vendor_name,
  COUNT(*) AS transaction_count,
  SUM(e.amount) AS total_amount,
  AVG(e.amount) AS avg_transaction_amount,
  AVG(e.ocr_confidence) AS avg_ocr_confidence,
  MAX(e.expense_date) AS last_transaction_date
FROM scout.silver_expenses e
WHERE e.vendor_name IS NOT NULL
GROUP BY e.tenant_id, e.vendor_name
HAVING COUNT(*) >= 5;

-- ============================================================================
-- Gold Views: BIR Compliance Analytics
-- ============================================================================

-- BIR Filing Status Dashboard
CREATE OR REPLACE VIEW scout.gold_bir_filing_status AS
SELECT
  b.tenant_id,
  b.form_type,
  b.filing_period,
  b.filing_deadline,
  b.status,
  b.filed_date,
  b.agency_name,
  b.employee_name,
  b.gross_income,
  b.withholding_tax,
  b.net_tax_due,
  CASE
    WHEN b.status = 'filed' AND b.filed_date <= b.filing_deadline THEN 'on_time'
    WHEN b.status = 'filed' AND b.filed_date > b.filing_deadline THEN 'late'
    WHEN b.status != 'filed' AND CURRENT_TIMESTAMP > b.filing_deadline THEN 'overdue'
    WHEN b.status != 'filed' AND CURRENT_TIMESTAMP > (b.filing_deadline - INTERVAL '3 days') THEN 'at_risk'
    ELSE 'on_track'
  END AS compliance_status,
  EXTRACT(DAY FROM (b.filing_deadline - CURRENT_TIMESTAMP)) AS days_until_deadline
FROM scout.silver_bir_forms b;

-- BIR Monthly Compliance Summary
CREATE OR REPLACE VIEW scout.gold_bir_monthly_summary AS
SELECT
  b.tenant_id,
  DATE_TRUNC('month', b.filing_deadline) AS month,
  b.form_type,
  COUNT(*) AS total_forms,
  COUNT(*) FILTER (WHERE b.status = 'filed') AS filed_count,
  COUNT(*) FILTER (WHERE b.status = 'filed' AND b.filed_date <= b.filing_deadline) AS on_time_count,
  COUNT(*) FILTER (WHERE b.status = 'filed' AND b.filed_date > b.filing_deadline) AS late_count,
  SUM(b.gross_income) AS total_gross_income,
  SUM(b.withholding_tax) AS total_withholding_tax,
  SUM(b.net_tax_due) AS total_net_tax_due
FROM scout.silver_bir_forms b
GROUP BY b.tenant_id, DATE_TRUNC('month', b.filing_deadline), b.form_type;

-- ============================================================================
-- Gold Views: PPM Analytics
-- ============================================================================

-- PPM Task Status Overview
CREATE OR REPLACE VIEW scout.gold_ppm_task_status AS
SELECT
  t.tenant_id,
  t.workspace_id,
  t.task_type,
  t.priority,
  t.status,
  t.logframe_level,
  COUNT(*) AS task_count,
  AVG(t.progress_pct) AS avg_progress,
  COUNT(*) FILTER (WHERE t.status = 'completed') AS completed_count,
  COUNT(*) FILTER (WHERE t.status = 'in_progress') AS in_progress_count,
  COUNT(*) FILTER (WHERE t.status = 'not_started') AS not_started_count,
  COUNT(*) FILTER (WHERE t.due_date < CURRENT_TIMESTAMP AND t.status != 'completed') AS overdue_count
FROM scout.silver_ppm_tasks t
GROUP BY t.tenant_id, t.workspace_id, t.task_type, t.priority, t.status, t.logframe_level;

-- PPM Upcoming Deadlines
CREATE OR REPLACE VIEW scout.gold_ppm_upcoming_deadlines AS
SELECT
  t.tenant_id,
  t.task_name,
  t.task_type,
  t.priority,
  t.status,
  t.due_date,
  t.assigned_to,
  t.responsible_role,
  t.progress_pct,
  EXTRACT(DAY FROM (t.due_date - CURRENT_TIMESTAMP)) AS days_until_due,
  CASE
    WHEN t.due_date < CURRENT_TIMESTAMP THEN 'overdue'
    WHEN t.due_date < (CURRENT_TIMESTAMP + INTERVAL '3 days') THEN 'urgent'
    WHEN t.due_date < (CURRENT_TIMESTAMP + INTERVAL '7 days') THEN 'upcoming'
    ELSE 'future'
  END AS urgency_level
FROM scout.silver_ppm_tasks t
WHERE t.status != 'completed'
  AND t.due_date IS NOT NULL
ORDER BY t.due_date ASC;

-- ============================================================================
-- Gold Views: Agency/Client Analytics
-- ============================================================================

-- Agency Financial Summary
CREATE OR REPLACE VIEW scout.gold_agency_summary AS
SELECT
  a.tenant_id,
  a.agency_code,
  a.agency_name,
  a.currency,
  a.status,
  a.account_manager,
  COUNT(DISTINCT e.id) AS expense_count,
  SUM(e.amount) AS total_expenses,
  COUNT(DISTINCT b.id) AS bir_form_count,
  COUNT(DISTINCT t.id) AS task_count
FROM scout.silver_agencies a
LEFT JOIN scout.silver_expenses e ON e.metadata->>'agency_code' = a.agency_code AND e.tenant_id = a.tenant_id
LEFT JOIN scout.silver_bir_forms b ON b.agency_name = a.agency_name AND b.tenant_id = a.tenant_id
LEFT JOIN scout.silver_ppm_tasks t ON t.metadata->>'agency_code' = a.agency_code AND t.tenant_id = a.tenant_id
GROUP BY a.tenant_id, a.agency_code, a.agency_name, a.currency, a.status, a.account_manager;

-- ============================================================================
-- Gold Views: Data Quality Monitoring
-- ============================================================================

-- Data Quality Scorecard
CREATE OR REPLACE VIEW scout.gold_data_quality_scorecard AS
SELECT
  'expenses' AS entity_type,
  e.tenant_id,
  COUNT(*) AS total_records,
  AVG(e.quality_score) AS avg_quality_score,
  COUNT(*) FILTER (WHERE e.quality_score >= 0.90) AS excellent_count,
  COUNT(*) FILTER (WHERE e.quality_score >= 0.80 AND e.quality_score < 0.90) AS good_count,
  COUNT(*) FILTER (WHERE e.quality_score < 0.80) AS poor_count,
  COUNT(*) FILTER (WHERE JSONB_ARRAY_LENGTH(e.validation_errors) = 0) AS zero_errors_count,
  COUNT(*) FILTER (WHERE JSONB_ARRAY_LENGTH(e.validation_errors) > 0) AS has_errors_count
FROM scout.silver_expenses e
GROUP BY e.tenant_id
UNION ALL
SELECT
  'bir_forms' AS entity_type,
  b.tenant_id,
  COUNT(*) AS total_records,
  AVG(b.quality_score) AS avg_quality_score,
  COUNT(*) FILTER (WHERE b.quality_score >= 0.90) AS excellent_count,
  COUNT(*) FILTER (WHERE b.quality_score >= 0.80 AND b.quality_score < 0.90) AS good_count,
  COUNT(*) FILTER (WHERE b.quality_score < 0.80) AS poor_count,
  COUNT(*) FILTER (WHERE JSONB_ARRAY_LENGTH(b.validation_errors) = 0) AS zero_errors_count,
  COUNT(*) FILTER (WHERE JSONB_ARRAY_LENGTH(b.validation_errors) > 0) AS has_errors_count
FROM scout.silver_bir_forms b
GROUP BY b.tenant_id;

-- ============================================================================
-- Gold Materialized Views for Performance
-- ============================================================================

-- Materialized view for expensive summary (refresh hourly)
CREATE MATERIALIZED VIEW IF NOT EXISTS scout.gold_expense_summary_mat AS
SELECT * FROM scout.gold_expense_summary;

CREATE UNIQUE INDEX IF NOT EXISTS idx_gold_expense_summary_mat_unique
  ON scout.gold_expense_summary_mat(tenant_id, workspace_id, month, category, currency);

-- Materialized view for BIR compliance (refresh daily)
CREATE MATERIALIZED VIEW IF NOT EXISTS scout.gold_bir_monthly_summary_mat AS
SELECT * FROM scout.gold_bir_monthly_summary;

CREATE UNIQUE INDEX IF NOT EXISTS idx_gold_bir_monthly_summary_mat_unique
  ON scout.gold_bir_monthly_summary_mat(tenant_id, month, form_type);

-- ============================================================================
-- Functions for Materialized View Refresh
-- ============================================================================

CREATE OR REPLACE FUNCTION scout.refresh_gold_materialized_views()
RETURNS void AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY scout.gold_expense_summary_mat;
  REFRESH MATERIALIZED VIEW CONCURRENTLY scout.gold_bir_monthly_summary_mat;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON VIEW scout.gold_expense_summary IS 'Expense analytics by category and month - pre-aggregated for BI dashboards';
COMMENT ON VIEW scout.gold_bir_filing_status IS 'Real-time BIR filing compliance dashboard with deadline tracking';
COMMENT ON VIEW scout.gold_ppm_task_status IS 'PPM task status overview with logframe breakdown';
COMMENT ON VIEW scout.gold_agency_summary IS 'Agency financial summary with cross-entity metrics';
COMMENT ON VIEW scout.gold_data_quality_scorecard IS 'Data quality monitoring across all Silver entities';

COMMENT ON MATERIALIZED VIEW scout.gold_expense_summary_mat IS 'Materialized expense summary - refresh hourly via cron';
COMMENT ON MATERIALIZED VIEW scout.gold_bir_monthly_summary_mat IS 'Materialized BIR summary - refresh daily at 6AM';
