-- Migration: 20241230000004_gold_views.sql
-- Description: Create gold layer aggregations and reporting views
-- Author: InsightPulseAI

-- =====================================================
-- Gold Layer: Daily Revenue Summary
-- =====================================================

CREATE MATERIALIZED VIEW gold.daily_revenue AS
SELECT
    invoice_date AS date,
    EXTRACT(YEAR FROM invoice_date) AS year,
    EXTRACT(MONTH FROM invoice_date) AS month,
    EXTRACT(DOW FROM invoice_date) AS day_of_week,
    move_type,
    COUNT(*) AS invoice_count,
    SUM(amount_untaxed) AS total_revenue,
    SUM(amount_tax) AS total_tax,
    SUM(amount_total) AS total_amount,
    AVG(amount_total) AS avg_invoice_amount,
    COUNT(DISTINCT partner_id) AS unique_customers
FROM silver.invoices
WHERE state = 'posted'
  AND move_type IN ('out_invoice', 'out_refund')
GROUP BY invoice_date, EXTRACT(YEAR FROM invoice_date),
         EXTRACT(MONTH FROM invoice_date), EXTRACT(DOW FROM invoice_date), move_type;

CREATE UNIQUE INDEX idx_gold_daily_revenue_pk ON gold.daily_revenue(date, move_type);

COMMENT ON MATERIALIZED VIEW gold.daily_revenue IS 'Daily revenue aggregation for dashboards';

-- =====================================================
-- Gold Layer: Monthly Close Summary
-- =====================================================

CREATE MATERIALIZED VIEW gold.monthly_close AS
SELECT
    DATE_TRUNC('month', invoice_date)::DATE AS month,
    EXTRACT(YEAR FROM invoice_date) AS year,
    EXTRACT(MONTH FROM invoice_date) AS month_num,
    -- Revenue
    SUM(CASE WHEN move_type = 'out_invoice' THEN amount_total ELSE 0 END) AS total_sales,
    SUM(CASE WHEN move_type = 'out_refund' THEN amount_total ELSE 0 END) AS total_refunds,
    SUM(CASE WHEN move_type = 'out_invoice' THEN amount_total ELSE -amount_total END) AS net_revenue,
    -- Expenses
    SUM(CASE WHEN move_type = 'in_invoice' THEN amount_total ELSE 0 END) AS total_purchases,
    SUM(CASE WHEN move_type = 'in_refund' THEN amount_total ELSE 0 END) AS purchase_refunds,
    -- Tax
    SUM(CASE WHEN move_type IN ('out_invoice', 'out_refund') THEN amount_tax ELSE 0 END) AS output_vat,
    SUM(CASE WHEN move_type IN ('in_invoice', 'in_refund') THEN amount_tax ELSE 0 END) AS input_vat,
    -- Counts
    COUNT(*) AS total_transactions,
    COUNT(DISTINCT partner_id) AS unique_partners
FROM silver.invoices
WHERE state = 'posted'
GROUP BY DATE_TRUNC('month', invoice_date), EXTRACT(YEAR FROM invoice_date), EXTRACT(MONTH FROM invoice_date);

CREATE UNIQUE INDEX idx_gold_monthly_close_pk ON gold.monthly_close(month);

COMMENT ON MATERIALIZED VIEW gold.monthly_close IS 'Monthly closing summary for finance';

-- =====================================================
-- Gold Layer: BIR Form 1601-C Summary (Monthly Withholding)
-- =====================================================

CREATE MATERIALIZED VIEW gold.bir_1601c_summary AS
SELECT
    DATE_TRUNC('month', date_from)::DATE AS month,
    EXTRACT(YEAR FROM date_from) AS year,
    EXTRACT(MONTH FROM date_from) AS month_num,
    COUNT(DISTINCT employee_id) AS employee_count,
    SUM(gross_salary) AS total_compensation,
    SUM(total_taxable) AS total_taxable_compensation,
    SUM(sss_contribution) AS total_sss,
    SUM(philhealth) AS total_philhealth,
    SUM(pagibig) AS total_pagibig,
    SUM(sss_contribution + philhealth + pagibig) AS total_mandatory_deductions,
    SUM(withholding_tax) AS total_withholding_tax,
    SUM(net_salary) AS total_net_salary,
    AVG(gross_salary) AS avg_salary
FROM silver.payslips
WHERE state = 'done'
GROUP BY DATE_TRUNC('month', date_from), EXTRACT(YEAR FROM date_from), EXTRACT(MONTH FROM date_from);

CREATE UNIQUE INDEX idx_gold_1601c_pk ON gold.bir_1601c_summary(month);

COMMENT ON MATERIALIZED VIEW gold.bir_1601c_summary IS 'Monthly payroll summary for BIR Form 1601-C';

-- =====================================================
-- Gold Layer: BIR Form 2550-Q Summary (Quarterly VAT)
-- =====================================================

CREATE MATERIALIZED VIEW gold.bir_2550q_summary AS
SELECT
    DATE_TRUNC('quarter', invoice_date)::DATE AS quarter,
    EXTRACT(YEAR FROM invoice_date) AS year,
    EXTRACT(QUARTER FROM invoice_date) AS quarter_num,
    -- Sales
    SUM(CASE WHEN move_type = 'out_invoice' THEN amount_untaxed ELSE 0 END) AS total_sales,
    SUM(CASE WHEN move_type = 'out_invoice' THEN amount_tax ELSE 0 END) AS output_vat,
    -- Purchases
    SUM(CASE WHEN move_type = 'in_invoice' THEN amount_untaxed ELSE 0 END) AS total_purchases,
    SUM(CASE WHEN move_type = 'in_invoice' THEN amount_tax ELSE 0 END) AS input_vat,
    -- Net VAT
    SUM(CASE WHEN move_type = 'out_invoice' THEN amount_tax ELSE 0 END) -
    SUM(CASE WHEN move_type = 'in_invoice' THEN amount_tax ELSE 0 END) AS net_vat_payable,
    -- Counts
    COUNT(CASE WHEN move_type = 'out_invoice' THEN 1 END) AS sales_invoice_count,
    COUNT(CASE WHEN move_type = 'in_invoice' THEN 1 END) AS purchase_invoice_count
FROM silver.invoices
WHERE state = 'posted'
  AND move_type IN ('out_invoice', 'in_invoice')
GROUP BY DATE_TRUNC('quarter', invoice_date), EXTRACT(YEAR FROM invoice_date), EXTRACT(QUARTER FROM invoice_date);

CREATE UNIQUE INDEX idx_gold_2550q_pk ON gold.bir_2550q_summary(quarter);

COMMENT ON MATERIALIZED VIEW gold.bir_2550q_summary IS 'Quarterly VAT summary for BIR Form 2550-Q';

-- =====================================================
-- Gold Layer: BIR Form 1700 Summary (Annual Income Tax)
-- =====================================================

CREATE MATERIALIZED VIEW gold.bir_1700_summary AS
SELECT
    EXTRACT(YEAR FROM date_from)::INTEGER AS tax_year,
    employee_id,
    MAX(employee_name) AS employee_name,
    SUM(gross_salary) AS annual_gross_income,
    SUM(total_taxable) AS annual_taxable_income,
    SUM(sss_contribution) AS annual_sss,
    SUM(philhealth) AS annual_philhealth,
    SUM(pagibig) AS annual_pagibig,
    SUM(withholding_tax) AS annual_tax_withheld,
    SUM(net_salary) AS annual_net_income,
    COUNT(*) AS payslip_count
FROM silver.payslips
WHERE state = 'done'
GROUP BY EXTRACT(YEAR FROM date_from), employee_id;

CREATE UNIQUE INDEX idx_gold_1700_pk ON gold.bir_1700_summary(tax_year, employee_id);

COMMENT ON MATERIALIZED VIEW gold.bir_1700_summary IS 'Annual income summary per employee for BIR Form 1700';

-- =====================================================
-- Gold Layer: Partner Aging Analysis
-- =====================================================

CREATE MATERIALIZED VIEW gold.partner_aging AS
SELECT
    i.partner_id,
    p.name AS partner_name,
    p.is_customer,
    p.is_vendor,
    SUM(CASE WHEN i.amount_residual > 0 AND i.due_date >= CURRENT_DATE THEN i.amount_residual ELSE 0 END) AS current_balance,
    SUM(CASE WHEN i.amount_residual > 0 AND i.due_date < CURRENT_DATE AND i.due_date >= CURRENT_DATE - 30 THEN i.amount_residual ELSE 0 END) AS days_1_30,
    SUM(CASE WHEN i.amount_residual > 0 AND i.due_date < CURRENT_DATE - 30 AND i.due_date >= CURRENT_DATE - 60 THEN i.amount_residual ELSE 0 END) AS days_31_60,
    SUM(CASE WHEN i.amount_residual > 0 AND i.due_date < CURRENT_DATE - 60 AND i.due_date >= CURRENT_DATE - 90 THEN i.amount_residual ELSE 0 END) AS days_61_90,
    SUM(CASE WHEN i.amount_residual > 0 AND i.due_date < CURRENT_DATE - 90 THEN i.amount_residual ELSE 0 END) AS over_90_days,
    SUM(i.amount_residual) AS total_outstanding,
    COUNT(*) AS open_invoice_count,
    MAX(i.invoice_date) AS last_invoice_date
FROM silver.invoices i
JOIN silver.partners p ON i.partner_id = p.odoo_id
WHERE i.state = 'posted'
  AND i.payment_state != 'paid'
  AND i.move_type IN ('out_invoice', 'in_invoice')
GROUP BY i.partner_id, p.name, p.is_customer, p.is_vendor;

CREATE UNIQUE INDEX idx_gold_aging_pk ON gold.partner_aging(partner_id);

COMMENT ON MATERIALIZED VIEW gold.partner_aging IS 'Accounts receivable/payable aging analysis';

-- =====================================================
-- Gold Layer: Dashboard KPIs
-- =====================================================

CREATE OR REPLACE VIEW gold.dashboard_kpis AS
SELECT
    -- Current Month Metrics
    (SELECT COALESCE(SUM(amount_total), 0) FROM silver.invoices
     WHERE move_type = 'out_invoice' AND state = 'posted'
     AND invoice_date >= DATE_TRUNC('month', CURRENT_DATE)) AS mtd_revenue,

    (SELECT COALESCE(SUM(amount_total), 0) FROM silver.invoices
     WHERE move_type = 'in_invoice' AND state = 'posted'
     AND invoice_date >= DATE_TRUNC('month', CURRENT_DATE)) AS mtd_expenses,

    (SELECT COUNT(DISTINCT partner_id) FROM silver.invoices
     WHERE move_type = 'out_invoice' AND state = 'posted'
     AND invoice_date >= DATE_TRUNC('month', CURRENT_DATE)) AS mtd_active_customers,

    -- Accounts Receivable
    (SELECT COALESCE(SUM(amount_residual), 0) FROM silver.invoices
     WHERE move_type = 'out_invoice' AND state = 'posted'
     AND payment_state != 'paid') AS total_ar,

    -- Accounts Payable
    (SELECT COALESCE(SUM(amount_residual), 0) FROM silver.invoices
     WHERE move_type = 'in_invoice' AND state = 'posted'
     AND payment_state != 'paid') AS total_ap,

    -- BIR Compliance
    (SELECT COUNT(*) FROM silver.bir_forms
     WHERE state NOT IN ('submitted', 'accepted')
     AND due_date <= CURRENT_DATE + 7) AS bir_forms_due_soon,

    -- Employee Count
    (SELECT COUNT(*) FROM silver.employees WHERE active = TRUE) AS active_employees,

    -- Payroll (Last Period)
    (SELECT COALESCE(SUM(net_salary), 0) FROM silver.payslips
     WHERE state = 'done'
     AND date_from >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
     AND date_from < DATE_TRUNC('month', CURRENT_DATE)) AS last_month_payroll;

COMMENT ON VIEW gold.dashboard_kpis IS 'Key performance indicators for executive dashboard';

-- =====================================================
-- Refresh Functions
-- =====================================================

CREATE OR REPLACE FUNCTION gold.refresh_all_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY gold.daily_revenue;
    REFRESH MATERIALIZED VIEW CONCURRENTLY gold.monthly_close;
    REFRESH MATERIALIZED VIEW CONCURRENTLY gold.bir_1601c_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY gold.bir_2550q_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY gold.bir_1700_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY gold.partner_aging;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION gold.refresh_all_materialized_views IS 'Refresh all gold layer materialized views';

-- Schedule refresh with pg_cron (if available)
-- SELECT cron.schedule('refresh-gold-views', '0 2 * * *', 'SELECT gold.refresh_all_materialized_views()');
