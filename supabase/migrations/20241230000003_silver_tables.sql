-- Migration: 20241230000003_silver_tables.sql
-- Description: Create silver layer tables for normalized business entities
-- Author: InsightPulseAI

-- =====================================================
-- Silver Layer: Partners (Customers/Vendors)
-- =====================================================

CREATE TABLE silver.partners (
    id BIGSERIAL PRIMARY KEY,
    odoo_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    partner_type VARCHAR(20) CHECK (partner_type IN ('contact', 'company', 'individual')),
    is_company BOOLEAN DEFAULT FALSE,
    is_customer BOOLEAN DEFAULT FALSE,
    is_vendor BOOLEAN DEFAULT FALSE,
    email VARCHAR(255),
    phone VARCHAR(50),
    mobile VARCHAR(50),
    vat VARCHAR(50),
    tin VARCHAR(50),
    street VARCHAR(255),
    street2 VARCHAR(255),
    city VARCHAR(100),
    state_name VARCHAR(100),
    zip VARCHAR(20),
    country_code VARCHAR(3),
    parent_id BIGINT REFERENCES silver.partners(odoo_id),
    credit_limit DECIMAL(15,2) DEFAULT 0,
    payment_term_days INTEGER DEFAULT 30,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    synced_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_silver_partners_name ON silver.partners(name);
CREATE INDEX idx_silver_partners_type ON silver.partners(partner_type);
CREATE INDEX idx_silver_partners_customer ON silver.partners(is_customer) WHERE is_customer = TRUE;
CREATE INDEX idx_silver_partners_vendor ON silver.partners(is_vendor) WHERE is_vendor = TRUE;

COMMENT ON TABLE silver.partners IS 'Normalized partner data (customers and vendors)';

-- =====================================================
-- Silver Layer: Employees
-- =====================================================

CREATE TABLE silver.employees (
    id BIGSERIAL PRIMARY KEY,
    odoo_id BIGINT UNIQUE NOT NULL,
    user_id UUID REFERENCES auth.users(id),
    name VARCHAR(255) NOT NULL,
    employee_code VARCHAR(50),
    email VARCHAR(255),
    phone VARCHAR(50),
    mobile VARCHAR(50),
    department_name VARCHAR(255),
    job_title VARCHAR(255),
    manager_id BIGINT REFERENCES silver.employees(odoo_id),
    -- BIR Compliance Fields
    bir_tin VARCHAR(50),
    sss_number VARCHAR(50),
    philhealth_number VARCHAR(50),
    pagibig_number VARCHAR(50),
    tax_status VARCHAR(20) CHECK (tax_status IN ('single', 'married', 'head_of_family')),
    is_minimum_wage_earner BOOLEAN DEFAULT FALSE,
    is_senior_citizen BOOLEAN DEFAULT FALSE,
    is_pwd BOOLEAN DEFAULT FALSE,
    -- Employment
    hire_date DATE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    synced_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_silver_employees_dept ON silver.employees(department_name);
CREATE INDEX idx_silver_employees_tin ON silver.employees(bir_tin) WHERE bir_tin IS NOT NULL;
CREATE INDEX idx_silver_employees_user ON silver.employees(user_id) WHERE user_id IS NOT NULL;

COMMENT ON TABLE silver.employees IS 'Normalized employee data with BIR compliance fields';

-- =====================================================
-- Silver Layer: Invoices (Account Moves)
-- =====================================================

CREATE TABLE silver.invoices (
    id BIGSERIAL PRIMARY KEY,
    odoo_id BIGINT UNIQUE NOT NULL,
    number VARCHAR(64) NOT NULL,
    partner_id BIGINT REFERENCES silver.partners(odoo_id),
    partner_name VARCHAR(255),
    move_type VARCHAR(20) NOT NULL CHECK (move_type IN (
        'entry', 'out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt'
    )),
    invoice_date DATE NOT NULL,
    due_date DATE,
    accounting_date DATE,
    currency_code VARCHAR(3) DEFAULT 'PHP',
    amount_untaxed DECIMAL(15,2) NOT NULL DEFAULT 0,
    amount_tax DECIMAL(15,2) NOT NULL DEFAULT 0,
    amount_total DECIMAL(15,2) NOT NULL DEFAULT 0,
    amount_residual DECIMAL(15,2) DEFAULT 0,
    state VARCHAR(20) NOT NULL CHECK (state IN ('draft', 'posted', 'cancel')),
    payment_state VARCHAR(20) CHECK (payment_state IN ('not_paid', 'partial', 'paid', 'reversed')),
    -- BIR Compliance Fields
    bir_form_type VARCHAR(32),
    vat_amount DECIMAL(15,2),
    withholding_tax DECIMAL(15,2),
    -- Approval
    approval_state VARCHAR(20) DEFAULT 'pending' CHECK (approval_state IN ('pending', 'approved', 'rejected')),
    approved_by UUID REFERENCES auth.users(id),
    approved_at TIMESTAMPTZ,
    -- Metadata
    reference VARCHAR(255),
    narration TEXT,
    company_id BIGINT,
    journal_name VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    synced_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_silver_invoices_partner ON silver.invoices(partner_id);
CREATE INDEX idx_silver_invoices_date ON silver.invoices(invoice_date);
CREATE INDEX idx_silver_invoices_state ON silver.invoices(state);
CREATE INDEX idx_silver_invoices_type ON silver.invoices(move_type);
CREATE INDEX idx_silver_invoices_bir ON silver.invoices(bir_form_type) WHERE bir_form_type IS NOT NULL;
CREATE INDEX idx_silver_invoices_approval ON silver.invoices(approval_state);

COMMENT ON TABLE silver.invoices IS 'Normalized invoice data with BIR compliance fields';

-- =====================================================
-- Silver Layer: Payments
-- =====================================================

CREATE TABLE silver.payments (
    id BIGSERIAL PRIMARY KEY,
    odoo_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(64) NOT NULL,
    partner_id BIGINT REFERENCES silver.partners(odoo_id),
    partner_name VARCHAR(255),
    payment_type VARCHAR(20) NOT NULL CHECK (payment_type IN ('inbound', 'outbound', 'transfer')),
    partner_type VARCHAR(20) CHECK (partner_type IN ('customer', 'supplier')),
    payment_date DATE NOT NULL,
    currency_code VARCHAR(3) DEFAULT 'PHP',
    amount DECIMAL(15,2) NOT NULL,
    state VARCHAR(20) NOT NULL CHECK (state IN ('draft', 'posted', 'cancelled', 'reconciled')),
    payment_method VARCHAR(50),
    journal_name VARCHAR(100),
    reference VARCHAR(255),
    memo TEXT,
    -- Approval
    approval_state VARCHAR(20) DEFAULT 'pending' CHECK (approval_state IN ('pending', 'approved', 'rejected')),
    approved_by UUID REFERENCES auth.users(id),
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    synced_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_silver_payments_partner ON silver.payments(partner_id);
CREATE INDEX idx_silver_payments_date ON silver.payments(payment_date);
CREATE INDEX idx_silver_payments_type ON silver.payments(payment_type);
CREATE INDEX idx_silver_payments_state ON silver.payments(state);

COMMENT ON TABLE silver.payments IS 'Normalized payment data';

-- =====================================================
-- Silver Layer: Payslips
-- =====================================================

CREATE TABLE silver.payslips (
    id BIGSERIAL PRIMARY KEY,
    odoo_id BIGINT UNIQUE NOT NULL,
    number VARCHAR(64) NOT NULL,
    employee_id BIGINT REFERENCES silver.employees(odoo_id),
    employee_name VARCHAR(255),
    date_from DATE NOT NULL,
    date_to DATE NOT NULL,
    -- Income
    gross_salary DECIMAL(15,2) NOT NULL DEFAULT 0,
    overtime_pay DECIMAL(15,2) DEFAULT 0,
    holiday_pay DECIMAL(15,2) DEFAULT 0,
    night_differential DECIMAL(15,2) DEFAULT 0,
    other_taxable DECIMAL(15,2) DEFAULT 0,
    total_taxable DECIMAL(15,2) NOT NULL DEFAULT 0,
    -- Non-Taxable
    thirteenth_month DECIMAL(15,2) DEFAULT 0,
    de_minimis DECIMAL(15,2) DEFAULT 0,
    -- Mandatory Deductions
    sss_contribution DECIMAL(15,2) DEFAULT 0,
    philhealth DECIMAL(15,2) DEFAULT 0,
    pagibig DECIMAL(15,2) DEFAULT 0,
    -- Tax
    withholding_tax DECIMAL(15,2) DEFAULT 0,
    tax_bracket VARCHAR(50),
    -- Net
    total_deductions DECIMAL(15,2) DEFAULT 0,
    net_salary DECIMAL(15,2) NOT NULL DEFAULT 0,
    -- State
    state VARCHAR(20) NOT NULL CHECK (state IN ('draft', 'verify', 'done', 'cancel')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    synced_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_silver_payslips_employee ON silver.payslips(employee_id);
CREATE INDEX idx_silver_payslips_date ON silver.payslips(date_from, date_to);
CREATE INDEX idx_silver_payslips_state ON silver.payslips(state);

COMMENT ON TABLE silver.payslips IS 'Normalized payslip data with BIR tax calculations';

-- =====================================================
-- Silver Layer: BIR Forms
-- =====================================================

CREATE TABLE silver.bir_forms (
    id BIGSERIAL PRIMARY KEY,
    odoo_id BIGINT UNIQUE,
    form_id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    form_code VARCHAR(32) NOT NULL,
    form_name VARCHAR(255),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    due_date DATE,
    filing_date DATE,
    -- Taxpayer Info
    company_name VARCHAR(255),
    tin VARCHAR(50),
    rdo_code VARCHAR(20),
    -- Amounts
    gross_amount DECIMAL(15,2) DEFAULT 0,
    taxable_amount DECIMAL(15,2) DEFAULT 0,
    tax_due DECIMAL(15,2) DEFAULT 0,
    tax_credits DECIMAL(15,2) DEFAULT 0,
    tax_payable DECIMAL(15,2) DEFAULT 0,
    penalties DECIMAL(15,2) DEFAULT 0,
    total_amount_due DECIMAL(15,2) DEFAULT 0,
    -- Form-specific data
    form_data JSONB,
    -- State
    state VARCHAR(20) NOT NULL CHECK (state IN ('draft', 'computed', 'validated', 'submitted', 'accepted', 'rejected', 'amended')),
    -- E-Filing
    confirmation_number VARCHAR(100),
    filing_reference VARCHAR(100),
    -- Metadata
    is_amendment BOOLEAN DEFAULT FALSE,
    original_form_id UUID REFERENCES silver.bir_forms(form_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    synced_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_silver_bir_forms_code ON silver.bir_forms(form_code);
CREATE INDEX idx_silver_bir_forms_period ON silver.bir_forms(period_start, period_end);
CREATE INDEX idx_silver_bir_forms_state ON silver.bir_forms(state);
CREATE INDEX idx_silver_bir_forms_due ON silver.bir_forms(due_date);

COMMENT ON TABLE silver.bir_forms IS 'BIR tax form data for all 36 form types';

-- =====================================================
-- Silver Layer: Audit Log
-- =====================================================

CREATE TABLE silver.audit_log (
    id BIGSERIAL PRIMARY KEY,
    audit_id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    table_name VARCHAR(100) NOT NULL,
    record_id BIGINT NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('create', 'update', 'delete', 'approve', 'reject')),
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[],
    user_id UUID REFERENCES auth.users(id),
    user_email VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_silver_audit_table ON silver.audit_log(table_name);
CREATE INDEX idx_silver_audit_record ON silver.audit_log(table_name, record_id);
CREATE INDEX idx_silver_audit_user ON silver.audit_log(user_id);
CREATE INDEX idx_silver_audit_date ON silver.audit_log(created_at);

COMMENT ON TABLE silver.audit_log IS 'Immutable audit trail for all silver layer changes';
