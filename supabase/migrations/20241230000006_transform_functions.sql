-- Migration: 20241230000006_transform_functions.sql
-- Description: Create transformation functions for bronze -> silver -> gold
-- Author: InsightPulseAI

-- =====================================================
-- Bronze -> Silver: Transform Invoices
-- =====================================================

CREATE OR REPLACE FUNCTION silver.transform_invoices()
RETURNS INTEGER AS $$
DECLARE
    rows_processed INTEGER := 0;
BEGIN
    -- Insert/upsert from bronze.odoo_records to silver.invoices
    INSERT INTO silver.invoices (
        odoo_id,
        number,
        partner_id,
        partner_name,
        move_type,
        invoice_date,
        due_date,
        accounting_date,
        currency_code,
        amount_untaxed,
        amount_tax,
        amount_total,
        amount_residual,
        state,
        payment_state,
        bir_form_type,
        vat_amount,
        withholding_tax,
        reference,
        narration,
        company_id,
        journal_name,
        synced_at
    )
    SELECT
        (odoo_data->>'id')::BIGINT,
        odoo_data->>'name',
        (odoo_data->'partner_id'->>0)::BIGINT,
        odoo_data->'partner_id'->>1,
        odoo_data->>'move_type',
        (odoo_data->>'invoice_date')::DATE,
        (odoo_data->>'invoice_date_due')::DATE,
        (odoo_data->>'date')::DATE,
        COALESCE(odoo_data->'currency_id'->>1, 'PHP'),
        COALESCE((odoo_data->>'amount_untaxed')::DECIMAL, 0),
        COALESCE((odoo_data->>'amount_tax')::DECIMAL, 0),
        COALESCE((odoo_data->>'amount_total')::DECIMAL, 0),
        COALESCE((odoo_data->>'amount_residual')::DECIMAL, 0),
        odoo_data->>'state',
        odoo_data->>'payment_state',
        -- BIR form type based on amount
        CASE
            WHEN (odoo_data->>'amount_total')::DECIMAL >= 250000 THEN '1700'
            WHEN odoo_data->>'move_type' IN ('out_invoice', 'out_refund') THEN '2550-Q'
            ELSE NULL
        END,
        COALESCE((odoo_data->>'amount_tax')::DECIMAL, 0) * 0.12,
        COALESCE((odoo_data->>'amount_untaxed')::DECIMAL, 0) * 0.10,
        odoo_data->>'ref',
        odoo_data->>'narration',
        (odoo_data->'company_id'->>0)::BIGINT,
        odoo_data->'journal_id'->>1,
        now()
    FROM bronze.odoo_records
    WHERE odoo_model = 'account.move'
      AND write_date > COALESCE(
          (SELECT MAX(synced_at) FROM silver.invoices),
          '1970-01-01'::TIMESTAMPTZ
      )
    ON CONFLICT (odoo_id) DO UPDATE SET
        number = EXCLUDED.number,
        partner_id = EXCLUDED.partner_id,
        partner_name = EXCLUDED.partner_name,
        move_type = EXCLUDED.move_type,
        invoice_date = EXCLUDED.invoice_date,
        due_date = EXCLUDED.due_date,
        accounting_date = EXCLUDED.accounting_date,
        currency_code = EXCLUDED.currency_code,
        amount_untaxed = EXCLUDED.amount_untaxed,
        amount_tax = EXCLUDED.amount_tax,
        amount_total = EXCLUDED.amount_total,
        amount_residual = EXCLUDED.amount_residual,
        state = EXCLUDED.state,
        payment_state = EXCLUDED.payment_state,
        bir_form_type = EXCLUDED.bir_form_type,
        vat_amount = EXCLUDED.vat_amount,
        withholding_tax = EXCLUDED.withholding_tax,
        reference = EXCLUDED.reference,
        narration = EXCLUDED.narration,
        company_id = EXCLUDED.company_id,
        journal_name = EXCLUDED.journal_name,
        updated_at = now(),
        synced_at = now();

    GET DIAGNOSTICS rows_processed = ROW_COUNT;

    RAISE NOTICE 'Transformed % invoice records', rows_processed;
    RETURN rows_processed;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- Bronze -> Silver: Transform Partners
-- =====================================================

CREATE OR REPLACE FUNCTION silver.transform_partners()
RETURNS INTEGER AS $$
DECLARE
    rows_processed INTEGER := 0;
BEGIN
    INSERT INTO silver.partners (
        odoo_id,
        name,
        display_name,
        partner_type,
        is_company,
        is_customer,
        is_vendor,
        email,
        phone,
        mobile,
        vat,
        tin,
        street,
        street2,
        city,
        state_name,
        zip,
        country_code,
        parent_id,
        credit_limit,
        active,
        synced_at
    )
    SELECT
        (odoo_data->>'id')::BIGINT,
        odoo_data->>'name',
        odoo_data->>'display_name',
        odoo_data->>'type',
        COALESCE((odoo_data->>'is_company')::BOOLEAN, FALSE),
        TRUE,  -- Default to customer
        FALSE, -- Default not vendor
        odoo_data->>'email',
        odoo_data->>'phone',
        odoo_data->>'mobile',
        odoo_data->>'vat',
        odoo_data->>'vat',  -- TIN = VAT in PH
        odoo_data->>'street',
        odoo_data->>'street2',
        odoo_data->>'city',
        odoo_data->'state_id'->>1,
        odoo_data->>'zip',
        odoo_data->'country_id'->>1,
        (odoo_data->'parent_id'->>0)::BIGINT,
        COALESCE((odoo_data->>'credit_limit')::DECIMAL, 0),
        COALESCE((odoo_data->>'active')::BOOLEAN, TRUE),
        now()
    FROM bronze.odoo_records
    WHERE odoo_model = 'res.partner'
      AND write_date > COALESCE(
          (SELECT MAX(synced_at) FROM silver.partners),
          '1970-01-01'::TIMESTAMPTZ
      )
    ON CONFLICT (odoo_id) DO UPDATE SET
        name = EXCLUDED.name,
        display_name = EXCLUDED.display_name,
        partner_type = EXCLUDED.partner_type,
        is_company = EXCLUDED.is_company,
        email = EXCLUDED.email,
        phone = EXCLUDED.phone,
        mobile = EXCLUDED.mobile,
        vat = EXCLUDED.vat,
        tin = EXCLUDED.tin,
        street = EXCLUDED.street,
        street2 = EXCLUDED.street2,
        city = EXCLUDED.city,
        state_name = EXCLUDED.state_name,
        zip = EXCLUDED.zip,
        country_code = EXCLUDED.country_code,
        parent_id = EXCLUDED.parent_id,
        credit_limit = EXCLUDED.credit_limit,
        active = EXCLUDED.active,
        updated_at = now(),
        synced_at = now();

    GET DIAGNOSTICS rows_processed = ROW_COUNT;

    RAISE NOTICE 'Transformed % partner records', rows_processed;
    RETURN rows_processed;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- Bronze -> Silver: Transform Employees
-- =====================================================

CREATE OR REPLACE FUNCTION silver.transform_employees()
RETURNS INTEGER AS $$
DECLARE
    rows_processed INTEGER := 0;
BEGIN
    INSERT INTO silver.employees (
        odoo_id,
        name,
        employee_code,
        email,
        phone,
        mobile,
        department_name,
        job_title,
        manager_id,
        bir_tin,
        sss_number,
        philhealth_number,
        pagibig_number,
        tax_status,
        is_minimum_wage_earner,
        is_senior_citizen,
        is_pwd,
        hire_date,
        active,
        synced_at
    )
    SELECT
        (odoo_data->>'id')::BIGINT,
        odoo_data->>'name',
        odoo_data->>'barcode',
        odoo_data->>'work_email',
        odoo_data->>'work_phone',
        odoo_data->>'mobile_phone',
        odoo_data->'department_id'->>1,
        odoo_data->'job_id'->>1,
        (odoo_data->'parent_id'->>0)::BIGINT,
        odoo_data->>'bir_tin',
        odoo_data->>'sss_number',
        odoo_data->>'philhealth_number',
        odoo_data->>'pagibig_number',
        COALESCE(odoo_data->>'tax_status', 'single'),
        COALESCE((odoo_data->>'is_minimum_wage_earner')::BOOLEAN, FALSE),
        COALESCE((odoo_data->>'is_senior_citizen')::BOOLEAN, FALSE),
        COALESCE((odoo_data->>'is_pwd')::BOOLEAN, FALSE),
        (odoo_data->>'joining_date')::DATE,
        COALESCE((odoo_data->>'active')::BOOLEAN, TRUE),
        now()
    FROM bronze.odoo_records
    WHERE odoo_model = 'hr.employee'
      AND write_date > COALESCE(
          (SELECT MAX(synced_at) FROM silver.employees),
          '1970-01-01'::TIMESTAMPTZ
      )
    ON CONFLICT (odoo_id) DO UPDATE SET
        name = EXCLUDED.name,
        employee_code = EXCLUDED.employee_code,
        email = EXCLUDED.email,
        phone = EXCLUDED.phone,
        mobile = EXCLUDED.mobile,
        department_name = EXCLUDED.department_name,
        job_title = EXCLUDED.job_title,
        manager_id = EXCLUDED.manager_id,
        bir_tin = EXCLUDED.bir_tin,
        sss_number = EXCLUDED.sss_number,
        philhealth_number = EXCLUDED.philhealth_number,
        pagibig_number = EXCLUDED.pagibig_number,
        tax_status = EXCLUDED.tax_status,
        is_minimum_wage_earner = EXCLUDED.is_minimum_wage_earner,
        is_senior_citizen = EXCLUDED.is_senior_citizen,
        is_pwd = EXCLUDED.is_pwd,
        hire_date = EXCLUDED.hire_date,
        active = EXCLUDED.active,
        updated_at = now(),
        synced_at = now();

    GET DIAGNOSTICS rows_processed = ROW_COUNT;

    RAISE NOTICE 'Transformed % employee records', rows_processed;
    RETURN rows_processed;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- Master Transform Function
-- =====================================================

CREATE OR REPLACE FUNCTION silver.run_all_transformations()
RETURNS TABLE (
    table_name TEXT,
    rows_processed INTEGER
) AS $$
BEGIN
    RETURN QUERY SELECT 'partners'::TEXT, silver.transform_partners();
    RETURN QUERY SELECT 'employees'::TEXT, silver.transform_employees();
    RETURN QUERY SELECT 'invoices'::TEXT, silver.transform_invoices();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION silver.run_all_transformations IS 'Run all bronze -> silver transformations';

-- =====================================================
-- Audit Log Trigger Function
-- =====================================================

CREATE OR REPLACE FUNCTION silver.audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO silver.audit_log (
        table_name,
        record_id,
        action,
        old_values,
        new_values,
        changed_fields,
        user_id
    )
    VALUES (
        TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        TG_OP,
        CASE WHEN TG_OP = 'DELETE' THEN to_jsonb(OLD) ELSE NULL END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN to_jsonb(NEW) ELSE NULL END,
        CASE WHEN TG_OP = 'UPDATE' THEN
            (SELECT array_agg(key) FROM jsonb_each(to_jsonb(NEW))
             WHERE to_jsonb(OLD)->key IS DISTINCT FROM to_jsonb(NEW)->key)
        ELSE NULL END,
        auth.uid()
    );

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create audit triggers on key tables
CREATE TRIGGER audit_invoices
    AFTER INSERT OR UPDATE OR DELETE ON silver.invoices
    FOR EACH ROW EXECUTE FUNCTION silver.audit_trigger_function();

CREATE TRIGGER audit_payments
    AFTER INSERT OR UPDATE OR DELETE ON silver.payments
    FOR EACH ROW EXECUTE FUNCTION silver.audit_trigger_function();

CREATE TRIGGER audit_bir_forms
    AFTER INSERT OR UPDATE OR DELETE ON silver.bir_forms
    FOR EACH ROW EXECUTE FUNCTION silver.audit_trigger_function();
