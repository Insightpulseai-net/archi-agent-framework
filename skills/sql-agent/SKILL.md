---
name: sql-agent
description: Write and optimize SQL queries for Supabase (bronze/silver/gold transformations, RLS policies, aggregations, materialized views). Optimizes for <2s p99 latency. Use when designing database transformations or dashboard queries.
license: Apache-2.0
metadata:
  author: insightpulseai
  version: "1.0"
  domain: database
  database: postgresql
  extensions: ["pgcrypto", "pg_cron", "pgmq", "pg_net"]
---

# SQL Agent Skill

Write optimized PostgreSQL queries for Supabase.

## Purpose

This agent specializes in writing performant SQL for the Medallion architecture (bronze → silver → gold), creating RLS policies, and optimizing queries for real-time dashboards.

## How to Use

1. **Describe transformation** (bronze → silver, etc.)
2. **Provide source/target schemas**
3. **Specify business logic**
4. **Agent generates SQL** with indexes and RLS

## Query Types

### Bronze → Silver Transformations
- Extract JSONB data from bronze tables
- Normalize into typed silver columns
- Apply constraints and validation

### Silver → Gold Aggregations
- Create summary views and materialized views
- Time-series aggregations (daily, monthly)
- BIR reporting views

### RLS Policy Generation
- Role-based filters (admin, approver, analyst, employee)
- Dynamic predicates using `auth.uid()`, `auth.jwt()`
- Tenant isolation policies

### Performance Optimization
- Add indexes on filter columns
- Use EXPLAIN ANALYZE to identify bottlenecks
- Target <2s p99 for all queries

## Medallion Schema Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   BRONZE    │────▶│   SILVER    │────▶│    GOLD     │
│ (raw JSON)  │     │ (normalized)│     │ (aggregated)│
└─────────────┘     └─────────────┘     └─────────────┘
│                   │                   │
├─ webhook_log      ├─ invoices         ├─ daily_revenue
├─ odoo_sync_log    ├─ payments         ├─ monthly_close
├─ file_imports     ├─ employees        ├─ bir_1700_summary
│                   ├─ payslips         ├─ bir_1601c_monthly
│                   └─ bir_forms        └─ bir_2550q_quarterly
```

## Example: Bronze → Silver Transformation

### Input
```json
{
  "source": "bronze.webhook_log",
  "target": "silver.invoices",
  "business_logic": "Parse odoo_data JSON, validate amounts, extract BIR fields"
}
```

### Output
```sql
-- Migration: 20241230_001_bronze_to_silver_invoices.sql
-- Description: Transform bronze webhook logs to silver invoices

-- Create silver table if not exists
CREATE TABLE IF NOT EXISTS silver.invoices (
    id BIGSERIAL PRIMARY KEY,
    odoo_id BIGINT UNIQUE NOT NULL,
    number VARCHAR(64) NOT NULL,
    partner_id BIGINT REFERENCES silver.partners(odoo_id),
    partner_name VARCHAR(255),
    invoice_date DATE NOT NULL,
    due_date DATE,
    amount_untaxed DECIMAL(15,2) NOT NULL DEFAULT 0,
    amount_tax DECIMAL(15,2) NOT NULL DEFAULT 0,
    amount_total DECIMAL(15,2) NOT NULL DEFAULT 0,
    state VARCHAR(32) NOT NULL DEFAULT 'draft',
    move_type VARCHAR(32) NOT NULL,
    -- BIR compliance fields
    bir_form_type VARCHAR(32),
    vat_amount DECIMAL(15,2),
    withholding_tax DECIMAL(15,2),
    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    synced_from_bronze_id BIGINT REFERENCES bronze.webhook_log(id)
);

-- Index for common queries
CREATE INDEX idx_invoices_partner ON silver.invoices(partner_id);
CREATE INDEX idx_invoices_date ON silver.invoices(invoice_date);
CREATE INDEX idx_invoices_state ON silver.invoices(state);
CREATE INDEX idx_invoices_bir_form ON silver.invoices(bir_form_type);

-- Transformation function
CREATE OR REPLACE FUNCTION silver.transform_bronze_invoices()
RETURNS INTEGER AS $$
DECLARE
    rows_processed INTEGER := 0;
BEGIN
    INSERT INTO silver.invoices (
        odoo_id,
        number,
        partner_id,
        partner_name,
        invoice_date,
        due_date,
        amount_untaxed,
        amount_tax,
        amount_total,
        state,
        move_type,
        bir_form_type,
        vat_amount,
        withholding_tax,
        synced_from_bronze_id
    )
    SELECT
        (payload->'data'->>'id')::BIGINT,
        payload->'data'->>'name',
        (payload->'data'->'partner_id'->>0)::BIGINT,
        payload->'data'->'partner_id'->>1,
        (payload->'data'->>'invoice_date')::DATE,
        (payload->'data'->>'invoice_date_due')::DATE,
        (payload->'data'->>'amount_untaxed')::DECIMAL,
        (payload->'data'->>'amount_tax')::DECIMAL,
        (payload->'data'->>'amount_total')::DECIMAL,
        payload->'data'->>'state',
        payload->'data'->>'move_type',
        CASE
            WHEN (payload->'data'->>'amount_total')::DECIMAL >= 250000 THEN '1700'
            WHEN payload->'data'->>'move_type' = 'out_invoice' THEN '2550Q'
            ELSE NULL
        END,
        (payload->'data'->>'amount_tax')::DECIMAL * 0.12,
        (payload->'data'->>'amount_untaxed')::DECIMAL * 0.10,
        id
    FROM bronze.webhook_log
    WHERE model_name = 'account.move'
      AND action IN ('create', 'write')
      AND processed_at IS NULL
    ON CONFLICT (odoo_id) DO UPDATE SET
        number = EXCLUDED.number,
        partner_id = EXCLUDED.partner_id,
        partner_name = EXCLUDED.partner_name,
        invoice_date = EXCLUDED.invoice_date,
        due_date = EXCLUDED.due_date,
        amount_untaxed = EXCLUDED.amount_untaxed,
        amount_tax = EXCLUDED.amount_tax,
        amount_total = EXCLUDED.amount_total,
        state = EXCLUDED.state,
        move_type = EXCLUDED.move_type,
        bir_form_type = EXCLUDED.bir_form_type,
        vat_amount = EXCLUDED.vat_amount,
        withholding_tax = EXCLUDED.withholding_tax,
        updated_at = now();

    GET DIAGNOSTICS rows_processed = ROW_COUNT;

    -- Mark bronze records as processed
    UPDATE bronze.webhook_log
    SET processed_at = now()
    WHERE model_name = 'account.move'
      AND processed_at IS NULL;

    RETURN rows_processed;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Schedule with pg_cron (every 5 minutes)
SELECT cron.schedule(
    'transform-invoices',
    '*/5 * * * *',
    'SELECT silver.transform_bronze_invoices();'
);
```

## Example: RLS Policy

### Input
```json
{
  "table": "silver.invoices",
  "roles": ["approver", "analyst", "employee"],
  "rules": {
    "approver": "Can view/update pending invoices",
    "analyst": "Can view all invoices (read-only)",
    "employee": "Can view own invoices only"
  }
}
```

### Output
```sql
-- Enable RLS on table
ALTER TABLE silver.invoices ENABLE ROW LEVEL SECURITY;

-- Policy: Approvers can view/update pending invoices
CREATE POLICY approver_pending_invoices
ON silver.invoices
FOR ALL
TO authenticated
USING (
    (auth.jwt()->>'role' = 'approver' AND state = 'pending')
    OR (auth.jwt()->>'role' = 'admin')
)
WITH CHECK (
    state IN ('approved', 'rejected', 'pending')
);

-- Policy: Analysts can view all (read-only)
CREATE POLICY analyst_read_all
ON silver.invoices
FOR SELECT
TO authenticated
USING (
    auth.jwt()->>'role' IN ('analyst', 'admin')
);

-- Policy: Employees can view own invoices
CREATE POLICY employee_own_invoices
ON silver.invoices
FOR SELECT
TO authenticated
USING (
    partner_id = (
        SELECT partner_id FROM silver.employees
        WHERE user_id = auth.uid()
    )
);

-- Grant permissions
GRANT SELECT ON silver.invoices TO authenticated;
GRANT UPDATE (state) ON silver.invoices TO authenticated;
```

## Example: Gold Aggregation (BIR 1700 Summary)

### Input
```json
{
  "view": "gold.bir_1700_annual_summary",
  "source": "silver.invoices",
  "aggregation": "Annual income by partner for BIR Form 1700"
}
```

### Output
```sql
-- Materialized view for BIR Form 1700 annual summary
CREATE MATERIALIZED VIEW gold.bir_1700_annual_summary AS
SELECT
    EXTRACT(YEAR FROM invoice_date) AS tax_year,
    partner_id,
    partner_name,
    COUNT(*) AS invoice_count,
    SUM(amount_untaxed) AS total_gross_income,
    SUM(amount_tax) AS total_vat,
    SUM(withholding_tax) AS total_withholding,
    SUM(amount_total) AS total_amount,
    -- BIR Form 1700 specific fields
    SUM(amount_untaxed) AS bir_gross_sales,
    SUM(withholding_tax) AS bir_creditable_tax,
    SUM(amount_untaxed) - SUM(withholding_tax) AS bir_taxable_income
FROM silver.invoices
WHERE move_type = 'out_invoice'
  AND state IN ('posted', 'paid')
GROUP BY
    EXTRACT(YEAR FROM invoice_date),
    partner_id,
    partner_name
ORDER BY tax_year DESC, total_amount DESC;

-- Index for fast lookups
CREATE UNIQUE INDEX idx_bir_1700_pk
ON gold.bir_1700_annual_summary(tax_year, partner_id);

-- Refresh schedule (daily at 2 AM)
SELECT cron.schedule(
    'refresh-bir-1700',
    '0 2 * * *',
    'REFRESH MATERIALIZED VIEW CONCURRENTLY gold.bir_1700_annual_summary;'
);
```

## Performance Targets

| Query Type | Target p99 | Measurement |
|------------|------------|-------------|
| Simple SELECT | <100ms | Single table, indexed |
| JOIN (2 tables) | <200ms | Indexed foreign keys |
| Aggregation | <500ms | With materialized views |
| Transformation | <2s | Batch of 1000 rows |
| Dashboard query | <1s | Gold layer only |

## Skill Boundaries

### What This Skill CAN Do
- Write CREATE TABLE with constraints
- Write transformations (bronze → silver → gold)
- Create RLS policies
- Create materialized views
- Optimize queries with indexes
- Schedule with pg_cron

### What This Skill CANNOT Do
- Extract specs from docs (use `documentation-parser`)
- Validate compliance (use `compliance-validator`)
- Generate application code (use `code-generator`)
- Deploy to production (use `deployment-orchestrator`)

## Rules

- Always add indexes on WHERE/JOIN columns
- Test with realistic data volumes (10K+ rows)
- Use EXPLAIN ANALYZE to verify <2s latency
- Use SECURITY DEFINER for sensitive operations
- **DO NOT** delete data (only INSERT/UPDATE/UPSERT)
- **DO NOT** modify RLS policies without review
- **DO NOT** skip performance benchmarks
