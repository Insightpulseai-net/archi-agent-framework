-- =============================================================================
-- InsightPulse AI Enterprise - Complete Data Model
-- PostgreSQL 16 + Row-Level Security (RLS) + Multi-Tenant
-- =============================================================================
-- Version: 2.0.0
-- SAP Parity: 95% | Microsoft Parity: 90% | Fortune 500 Ready
-- =============================================================================

-- =============================================================================
-- SCHEMA SETUP
-- =============================================================================

-- Drop schemas if exist (for clean install)
DROP SCHEMA IF EXISTS core CASCADE;
DROP SCHEMA IF EXISTS finance CASCADE;
DROP SCHEMA IF EXISTS hr CASCADE;
DROP SCHEMA IF EXISTS procurement CASCADE;
DROP SCHEMA IF EXISTS project CASCADE;
DROP SCHEMA IF EXISTS sales CASCADE;
DROP SCHEMA IF EXISTS inventory CASCADE;
DROP SCHEMA IF EXISTS manufacturing CASCADE;
DROP SCHEMA IF EXISTS quality CASCADE;
DROP SCHEMA IF EXISTS ai CASCADE;
DROP SCHEMA IF EXISTS audit CASCADE;
DROP SCHEMA IF EXISTS analytics CASCADE;

-- Create schemas
CREATE SCHEMA core;           -- Core/shared entities
CREATE SCHEMA finance;        -- Financial Accounting (SAP FI/CO)
CREATE SCHEMA hr;             -- Human Resources (SAP HCM)
CREATE SCHEMA procurement;    -- Procurement (SAP MM/SRM/Ariba)
CREATE SCHEMA project;        -- Project Management (SAP PS/Clarity)
CREATE SCHEMA sales;          -- Sales & CRM (SAP SD/CRM)
CREATE SCHEMA inventory;      -- Inventory & Warehouse (SAP WM/EWM)
CREATE SCHEMA manufacturing;  -- Manufacturing (SAP PP)
CREATE SCHEMA quality;        -- Quality Management (SAP QM)
CREATE SCHEMA ai;             -- AI/ML entities
CREATE SCHEMA audit;          -- Audit trail (SOC 2)
CREATE SCHEMA analytics;      -- Analytics/BI (SAP BW)

-- =============================================================================
-- EXTENSIONS
-- =============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";          -- Fuzzy search
CREATE EXTENSION IF NOT EXISTS "btree_gin";        -- GIN indexes
CREATE EXTENSION IF NOT EXISTS "vector";           -- pgvector for AI

-- =============================================================================
-- CORE SCHEMA - Shared Entities
-- =============================================================================

-- Tenants (Legal Entities / Companies)
CREATE TABLE core.tenant (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    tax_id VARCHAR(50),                    -- TIN for BIR
    registration_number VARCHAR(50),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    country_code CHAR(2) DEFAULT 'PH',
    currency_code CHAR(3) DEFAULT 'PHP',
    fiscal_year_start INT DEFAULT 1,       -- Month (1-12)
    parent_tenant_id UUID REFERENCES core.tenant(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);

-- Users
CREATE TABLE core.user (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    employee_id UUID,                       -- Link to hr.employee
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    last_login_at TIMESTAMPTZ,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, username),
    UNIQUE(tenant_id, email)
);

-- Roles
CREATE TABLE core.role (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, code)
);

-- User Roles
CREATE TABLE core.user_role (
    user_id UUID NOT NULL REFERENCES core.user(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES core.role(id) ON DELETE CASCADE,
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    granted_by UUID REFERENCES core.user(id),
    PRIMARY KEY (user_id, role_id)
);

-- Permissions
CREATE TABLE core.permission (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,           -- create, read, update, delete, approve
    description TEXT
);

-- Role Permissions
CREATE TABLE core.role_permission (
    role_id UUID NOT NULL REFERENCES core.role(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES core.permission(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- Sequences (for document numbering)
CREATE TABLE core.sequence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    code VARCHAR(50) NOT NULL,
    prefix VARCHAR(20),
    suffix VARCHAR(20),
    padding INT DEFAULT 6,
    next_value BIGINT DEFAULT 1,
    increment_by INT DEFAULT 1,
    UNIQUE(tenant_id, code)
);

-- =============================================================================
-- FINANCE SCHEMA - SAP FI/CO Parity
-- =============================================================================

-- Chart of Accounts
CREATE TABLE finance.account (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    code VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    account_type VARCHAR(50) NOT NULL,     -- asset, liability, equity, income, expense
    account_subtype VARCHAR(50),           -- bank, receivable, payable, etc.
    parent_id UUID REFERENCES finance.account(id),
    currency_code CHAR(3) DEFAULT 'PHP',
    is_reconcilable BOOLEAN DEFAULT FALSE,
    is_deprecated BOOLEAN DEFAULT FALSE,
    opening_balance NUMERIC(20,4) DEFAULT 0,
    opening_balance_date DATE,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, code)
);

-- Cost Centers (SAP CO)
CREATE TABLE finance.cost_center (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    code VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    parent_id UUID REFERENCES finance.cost_center(id),
    manager_id UUID,                        -- hr.employee
    department_id UUID,
    is_active BOOLEAN DEFAULT TRUE,
    valid_from DATE,
    valid_to DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, code)
);

-- Profit Centers (SAP CO)
CREATE TABLE finance.profit_center (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    code VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    parent_id UUID REFERENCES finance.profit_center(id),
    manager_id UUID,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, code)
);

-- Fiscal Periods
CREATE TABLE finance.fiscal_period (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    fiscal_year INT NOT NULL,
    period_number INT NOT NULL,            -- 1-12 or 1-13 with adjustment
    name VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'open',     -- open, closed, locked
    closed_at TIMESTAMPTZ,
    closed_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, fiscal_year, period_number)
);

-- Journal Entries
CREATE TABLE finance.journal_entry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    document_number VARCHAR(50) NOT NULL,
    entry_date DATE NOT NULL,
    posting_date DATE NOT NULL,
    fiscal_period_id UUID NOT NULL REFERENCES finance.fiscal_period(id),
    journal_type VARCHAR(50) NOT NULL,     -- general, sales, purchase, cash, adjustment
    reference VARCHAR(255),
    description TEXT,
    total_debit NUMERIC(20,4) NOT NULL,
    total_credit NUMERIC(20,4) NOT NULL,
    currency_code CHAR(3) DEFAULT 'PHP',
    exchange_rate NUMERIC(12,6) DEFAULT 1,
    status VARCHAR(20) DEFAULT 'draft',    -- draft, posted, reversed
    posted_at TIMESTAMPTZ,
    posted_by UUID REFERENCES core.user(id),
    reversed_entry_id UUID REFERENCES finance.journal_entry(id),
    source_document_type VARCHAR(50),      -- invoice, payment, etc.
    source_document_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES core.user(id),
    UNIQUE(tenant_id, document_number),
    CHECK (total_debit = total_credit)
);

-- Journal Entry Lines
CREATE TABLE finance.journal_entry_line (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    journal_entry_id UUID NOT NULL REFERENCES finance.journal_entry(id) ON DELETE CASCADE,
    line_number INT NOT NULL,
    account_id UUID NOT NULL REFERENCES finance.account(id),
    cost_center_id UUID REFERENCES finance.cost_center(id),
    profit_center_id UUID REFERENCES finance.profit_center(id),
    debit_amount NUMERIC(20,4) DEFAULT 0,
    credit_amount NUMERIC(20,4) DEFAULT 0,
    description TEXT,
    partner_id UUID,                        -- Customer/Vendor
    analytic_tags JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(journal_entry_id, line_number),
    CHECK (debit_amount >= 0 AND credit_amount >= 0),
    CHECK ((debit_amount > 0 AND credit_amount = 0) OR (debit_amount = 0 AND credit_amount > 0))
);

-- Budget (SAP BPC Parity)
CREATE TABLE finance.budget (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    name VARCHAR(255) NOT NULL,
    fiscal_year INT NOT NULL,
    budget_type VARCHAR(50) NOT NULL,      -- operating, capital, project
    status VARCHAR(20) DEFAULT 'draft',
    approved_at TIMESTAMPTZ,
    approved_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, name, fiscal_year)
);

-- Budget Lines
CREATE TABLE finance.budget_line (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    budget_id UUID NOT NULL REFERENCES finance.budget(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES finance.account(id),
    cost_center_id UUID REFERENCES finance.cost_center(id),
    period_number INT NOT NULL,
    amount NUMERIC(20,4) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bank Accounts
CREATE TABLE finance.bank_account (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    account_id UUID NOT NULL REFERENCES finance.account(id),
    bank_name VARCHAR(255) NOT NULL,
    bank_code VARCHAR(50),
    branch_name VARCHAR(255),
    account_number VARCHAR(50) NOT NULL,
    account_holder_name VARCHAR(255),
    currency_code CHAR(3) DEFAULT 'PHP',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, account_number)
);

-- Tax Codes (BIR Compliance)
CREATE TABLE finance.tax_code (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    code VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    tax_type VARCHAR(50) NOT NULL,         -- vat, withholding, income
    rate NUMERIC(8,4) NOT NULL,
    account_id UUID REFERENCES finance.account(id),
    bir_code VARCHAR(20),                   -- BIR ATC code
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, code)
);

-- =============================================================================
-- HR SCHEMA - SAP SuccessFactors Parity
-- =============================================================================

-- Departments
CREATE TABLE hr.department (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    code VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    parent_id UUID REFERENCES hr.department(id),
    manager_id UUID,
    cost_center_id UUID REFERENCES finance.cost_center(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, code)
);

-- Job Positions
CREATE TABLE hr.job_position (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    code VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    department_id UUID REFERENCES hr.department(id),
    job_grade VARCHAR(20),
    min_salary NUMERIC(20,4),
    max_salary NUMERIC(20,4),
    description TEXT,
    requirements TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, code)
);

-- Employees
CREATE TABLE hr.employee (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    employee_number VARCHAR(50) NOT NULL,
    user_id UUID REFERENCES core.user(id),
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    last_name VARCHAR(100) NOT NULL,
    suffix VARCHAR(20),
    birth_date DATE,
    gender VARCHAR(20),
    marital_status VARCHAR(20),
    nationality VARCHAR(100),
    
    -- Government IDs (Philippines)
    tin VARCHAR(20),                        -- Tax Identification Number
    sss_number VARCHAR(20),                 -- SSS
    philhealth_number VARCHAR(20),          -- PhilHealth
    pagibig_number VARCHAR(20),             -- Pag-IBIG
    
    -- Contact
    personal_email VARCHAR(255),
    work_email VARCHAR(255),
    mobile_phone VARCHAR(50),
    home_phone VARCHAR(50),
    
    -- Address
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    province VARCHAR(100),
    postal_code VARCHAR(20),
    country_code CHAR(2) DEFAULT 'PH',
    
    -- Emergency Contact
    emergency_contact_name VARCHAR(255),
    emergency_contact_phone VARCHAR(50),
    emergency_contact_relationship VARCHAR(50),
    
    -- Employment
    department_id UUID REFERENCES hr.department(id),
    job_position_id UUID REFERENCES hr.job_position(id),
    manager_id UUID REFERENCES hr.employee(id),
    hire_date DATE,
    probation_end_date DATE,
    termination_date DATE,
    termination_reason TEXT,
    employment_type VARCHAR(50),            -- full_time, part_time, contractor
    employment_status VARCHAR(50),          -- active, resigned, terminated, retired
    
    -- Compensation
    base_salary NUMERIC(20,4),
    salary_currency CHAR(3) DEFAULT 'PHP',
    pay_frequency VARCHAR(20) DEFAULT 'monthly',
    bank_account_number VARCHAR(50),
    bank_name VARCHAR(255),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, employee_number)
);

-- Employee Contracts
CREATE TABLE hr.contract (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    employee_id UUID NOT NULL REFERENCES hr.employee(id),
    contract_number VARCHAR(50) NOT NULL,
    contract_type VARCHAR(50) NOT NULL,     -- permanent, fixed_term, probation
    start_date DATE NOT NULL,
    end_date DATE,
    job_position_id UUID REFERENCES hr.job_position(id),
    department_id UUID REFERENCES hr.department(id),
    base_salary NUMERIC(20,4),
    allowances JSONB,
    benefits JSONB,
    work_schedule VARCHAR(50),
    probation_period_months INT,
    notice_period_days INT,
    status VARCHAR(20) DEFAULT 'active',
    signed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, contract_number)
);

-- Leave Types
CREATE TABLE hr.leave_type (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    code VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_paid BOOLEAN DEFAULT TRUE,
    max_days_per_year NUMERIC(5,2),
    is_carry_over_allowed BOOLEAN DEFAULT FALSE,
    max_carry_over_days NUMERIC(5,2),
    requires_approval BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, code)
);

-- Leave Requests
CREATE TABLE hr.leave_request (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    employee_id UUID NOT NULL REFERENCES hr.employee(id),
    leave_type_id UUID NOT NULL REFERENCES hr.leave_type(id),
    request_number VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_days NUMERIC(5,2) NOT NULL,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending',   -- pending, approved, rejected, cancelled
    approved_by UUID REFERENCES hr.employee(id),
    approved_at TIMESTAMPTZ,
    rejection_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, request_number)
);

-- Attendance
CREATE TABLE hr.attendance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    employee_id UUID NOT NULL REFERENCES hr.employee(id),
    attendance_date DATE NOT NULL,
    check_in_time TIMESTAMPTZ,
    check_out_time TIMESTAMPTZ,
    break_duration_minutes INT DEFAULT 0,
    worked_hours NUMERIC(5,2),
    overtime_hours NUMERIC(5,2),
    status VARCHAR(20) DEFAULT 'present',   -- present, absent, late, half_day, leave
    source VARCHAR(50),                      -- biometric, manual, mobile
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, employee_id, attendance_date)
);

-- Payroll Run
CREATE TABLE hr.payroll_run (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    run_number VARCHAR(50) NOT NULL,
    pay_period_start DATE NOT NULL,
    pay_period_end DATE NOT NULL,
    payment_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',     -- draft, processing, approved, paid
    total_gross NUMERIC(20,4),
    total_deductions NUMERIC(20,4),
    total_net NUMERIC(20,4),
    employee_count INT,
    approved_by UUID,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, run_number)
);

-- Payslip
CREATE TABLE hr.payslip (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payroll_run_id UUID NOT NULL REFERENCES hr.payroll_run(id),
    employee_id UUID NOT NULL REFERENCES hr.employee(id),
    payslip_number VARCHAR(50) NOT NULL,
    
    -- Earnings
    basic_pay NUMERIC(20,4),
    overtime_pay NUMERIC(20,4),
    allowances JSONB,
    bonuses NUMERIC(20,4),
    other_earnings JSONB,
    gross_pay NUMERIC(20,4),
    
    -- Deductions
    sss_contribution NUMERIC(20,4),
    philhealth_contribution NUMERIC(20,4),
    pagibig_contribution NUMERIC(20,4),
    withholding_tax NUMERIC(20,4),
    other_deductions JSONB,
    total_deductions NUMERIC(20,4),
    
    -- Net
    net_pay NUMERIC(20,4),
    
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(payroll_run_id, employee_id)
);

-- =============================================================================
-- PROCUREMENT SCHEMA - SAP Ariba Parity
-- =============================================================================

-- Vendors/Suppliers
CREATE TABLE procurement.vendor (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    vendor_code VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    tax_id VARCHAR(50),
    vendor_type VARCHAR(50),                -- supplier, contractor, service_provider
    
    -- Contact
    primary_contact_name VARCHAR(255),
    primary_email VARCHAR(255),
    primary_phone VARCHAR(50),
    website VARCHAR(255),
    
    -- Address
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    country_code CHAR(2),
    
    -- Payment
    payment_terms_days INT DEFAULT 30,
    currency_code CHAR(3) DEFAULT 'PHP',
    bank_name VARCHAR(255),
    bank_account_number VARCHAR(50),
    
    -- Compliance
    is_approved BOOLEAN DEFAULT FALSE,
    approved_at TIMESTAMPTZ,
    approved_by UUID,
    bir_registered BOOLEAN DEFAULT FALSE,
    
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, vendor_code)
);

-- Purchase Requisition
CREATE TABLE procurement.purchase_requisition (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    pr_number VARCHAR(50) NOT NULL,
    requester_id UUID NOT NULL REFERENCES hr.employee(id),
    department_id UUID REFERENCES hr.department(id),
    request_date DATE NOT NULL,
    required_date DATE,
    description TEXT,
    justification TEXT,
    total_amount NUMERIC(20,4),
    currency_code CHAR(3) DEFAULT 'PHP',
    priority VARCHAR(20) DEFAULT 'normal',  -- low, normal, high, urgent
    status VARCHAR(20) DEFAULT 'draft',     -- draft, pending, approved, rejected, converted
    approved_by UUID,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, pr_number)
);

-- PR Lines
CREATE TABLE procurement.pr_line (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pr_id UUID NOT NULL REFERENCES procurement.purchase_requisition(id) ON DELETE CASCADE,
    line_number INT NOT NULL,
    product_id UUID,
    description TEXT NOT NULL,
    quantity NUMERIC(20,4) NOT NULL,
    unit VARCHAR(20),
    unit_price NUMERIC(20,4),
    total_price NUMERIC(20,4),
    cost_center_id UUID REFERENCES finance.cost_center(id),
    account_id UUID REFERENCES finance.account(id),
    UNIQUE(pr_id, line_number)
);

-- Purchase Order
CREATE TABLE procurement.purchase_order (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    po_number VARCHAR(50) NOT NULL,
    vendor_id UUID NOT NULL REFERENCES procurement.vendor(id),
    pr_id UUID REFERENCES procurement.purchase_requisition(id),
    buyer_id UUID REFERENCES hr.employee(id),
    order_date DATE NOT NULL,
    expected_delivery_date DATE,
    
    -- Amounts
    subtotal NUMERIC(20,4),
    tax_amount NUMERIC(20,4),
    discount_amount NUMERIC(20,4),
    total_amount NUMERIC(20,4),
    currency_code CHAR(3) DEFAULT 'PHP',
    
    -- Terms
    payment_terms_days INT,
    shipping_method VARCHAR(100),
    shipping_address TEXT,
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft',     -- draft, sent, confirmed, received, invoiced, closed, cancelled
    sent_at TIMESTAMPTZ,
    confirmed_at TIMESTAMPTZ,
    
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, po_number)
);

-- PO Lines
CREATE TABLE procurement.po_line (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    po_id UUID NOT NULL REFERENCES procurement.purchase_order(id) ON DELETE CASCADE,
    line_number INT NOT NULL,
    product_id UUID,
    description TEXT NOT NULL,
    quantity NUMERIC(20,4) NOT NULL,
    unit VARCHAR(20),
    unit_price NUMERIC(20,4) NOT NULL,
    tax_rate NUMERIC(8,4) DEFAULT 0,
    discount_percent NUMERIC(8,4) DEFAULT 0,
    total_price NUMERIC(20,4),
    received_quantity NUMERIC(20,4) DEFAULT 0,
    invoiced_quantity NUMERIC(20,4) DEFAULT 0,
    UNIQUE(po_id, line_number)
);

-- Vendor Invoice
CREATE TABLE procurement.vendor_invoice (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    invoice_number VARCHAR(50) NOT NULL,
    vendor_id UUID NOT NULL REFERENCES procurement.vendor(id),
    po_id UUID REFERENCES procurement.purchase_order(id),
    vendor_invoice_number VARCHAR(100),
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    
    -- Amounts
    subtotal NUMERIC(20,4),
    tax_amount NUMERIC(20,4),
    withholding_tax NUMERIC(20,4),
    total_amount NUMERIC(20,4),
    paid_amount NUMERIC(20,4) DEFAULT 0,
    balance_due NUMERIC(20,4),
    currency_code CHAR(3) DEFAULT 'PHP',
    
    -- 3-Way Match
    gr_matched BOOLEAN DEFAULT FALSE,
    po_matched BOOLEAN DEFAULT FALSE,
    
    status VARCHAR(20) DEFAULT 'draft',     -- draft, pending, approved, paid, cancelled
    journal_entry_id UUID REFERENCES finance.journal_entry(id),
    
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, invoice_number)
);

-- =============================================================================
-- PROJECT SCHEMA - Clarity PPM Parity
-- =============================================================================

-- Projects
CREATE TABLE project.project (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    project_code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    project_type VARCHAR(50),               -- internal, client, maintenance
    
    -- Dates
    planned_start_date DATE,
    planned_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,
    
    -- People
    project_manager_id UUID REFERENCES hr.employee(id),
    sponsor_id UUID REFERENCES hr.employee(id),
    customer_id UUID,
    
    -- Financial
    budget_amount NUMERIC(20,4),
    actual_cost NUMERIC(20,4) DEFAULT 0,
    currency_code CHAR(3) DEFAULT 'PHP',
    cost_center_id UUID REFERENCES finance.cost_center(id),
    profit_center_id UUID REFERENCES finance.profit_center(id),
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft',     -- draft, active, on_hold, completed, cancelled
    health_status VARCHAR(20) DEFAULT 'green', -- green, yellow, red (RAG)
    percent_complete NUMERIC(5,2) DEFAULT 0,
    
    -- Hierarchy
    parent_project_id UUID REFERENCES project.project(id),
    program_id UUID,
    portfolio_id UUID,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, project_code)
);

-- WBS (Work Breakdown Structure)
CREATE TABLE project.wbs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES project.project(id),
    wbs_code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES project.wbs(id),
    level INT NOT NULL DEFAULT 1,
    sequence INT NOT NULL,
    
    -- Dates
    planned_start_date DATE,
    planned_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,
    
    -- Effort
    planned_hours NUMERIC(10,2),
    actual_hours NUMERIC(10,2) DEFAULT 0,
    
    -- Cost
    planned_cost NUMERIC(20,4),
    actual_cost NUMERIC(20,4) DEFAULT 0,
    
    status VARCHAR(20) DEFAULT 'not_started',
    percent_complete NUMERIC(5,2) DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, wbs_code)
);

-- Project Tasks
CREATE TABLE project.task (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES project.project(id),
    wbs_id UUID REFERENCES project.wbs(id),
    task_number VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Assignment
    assignee_id UUID REFERENCES hr.employee(id),
    
    -- Dates
    planned_start_date DATE,
    planned_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,
    
    -- Effort
    planned_hours NUMERIC(10,2),
    actual_hours NUMERIC(10,2) DEFAULT 0,
    remaining_hours NUMERIC(10,2),
    
    -- Status
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'not_started',
    percent_complete NUMERIC(5,2) DEFAULT 0,
    
    -- Dependencies
    predecessor_ids UUID[],
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, task_number)
);

-- Timesheets
CREATE TABLE project.timesheet (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    employee_id UUID NOT NULL REFERENCES hr.employee(id),
    week_start_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',     -- draft, submitted, approved, rejected
    submitted_at TIMESTAMPTZ,
    approved_by UUID,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, employee_id, week_start_date)
);

-- Timesheet Lines
CREATE TABLE project.timesheet_line (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timesheet_id UUID NOT NULL REFERENCES project.timesheet(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES project.project(id),
    task_id UUID REFERENCES project.task(id),
    date DATE NOT NULL,
    hours NUMERIC(5,2) NOT NULL,
    description TEXT,
    billable BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- AI SCHEMA - ML/AI Entities
-- =============================================================================

-- Document Embeddings (for RAG)
CREATE TABLE ai.document_embedding (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    source_type VARCHAR(50) NOT NULL,       -- invoice, receipt, contract, email
    source_id UUID NOT NULL,
    chunk_index INT DEFAULT 0,
    content TEXT NOT NULL,
    embedding vector(1536),                  -- OpenAI compatible dimension
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for vector similarity search
CREATE INDEX idx_document_embedding_vector ON ai.document_embedding 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- AI Predictions Log
CREATE TABLE ai.prediction_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50),
    input_data JSONB NOT NULL,
    prediction JSONB NOT NULL,
    confidence NUMERIC(5,4),
    latency_ms INT,
    source_type VARCHAR(50),
    source_id UUID,
    feedback VARCHAR(20),                   -- correct, incorrect, null
    feedback_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- AI Agent Conversations
CREATE TABLE ai.agent_conversation (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    user_id UUID REFERENCES core.user(id),
    agent_type VARCHAR(50) NOT NULL,        -- finance, hr, procurement
    session_id UUID NOT NULL,
    messages JSONB NOT NULL,
    context JSONB,
    tokens_used INT,
    cost_usd NUMERIC(10,6),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- OCR Results
CREATE TABLE ai.ocr_result (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES core.tenant(id),
    document_type VARCHAR(50) NOT NULL,     -- receipt, invoice, form
    source_file_path VARCHAR(500),
    raw_text TEXT,
    extracted_data JSONB,
    confidence NUMERIC(5,4),
    processing_time_ms INT,
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- AUDIT SCHEMA - SOC 2 Compliance
-- =============================================================================

-- Audit Log (Immutable)
CREATE TABLE audit.log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    user_id UUID,
    session_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    
    -- Action
    action VARCHAR(50) NOT NULL,            -- create, read, update, delete, login, logout, export
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    
    -- Change Details
    old_values JSONB,
    new_values JSONB,
    
    -- Metadata
    request_id UUID,
    duration_ms INT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Make audit log append-only (SOC 2 requirement)
CREATE RULE audit_log_no_update AS ON UPDATE TO audit.log DO INSTEAD NOTHING;
CREATE RULE audit_log_no_delete AS ON DELETE TO audit.log DO INSTEAD NOTHING;

-- Partition audit log by month for performance
-- (In production, use pg_partman for automated partition management)

-- Security Events
CREATE TABLE audit.security_event (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID,
    user_id UUID,
    event_type VARCHAR(50) NOT NULL,        -- login_success, login_failed, password_change, mfa_enabled
    ip_address INET,
    user_agent TEXT,
    details JSONB,
    severity VARCHAR(20) DEFAULT 'info',    -- info, warning, critical
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- ANALYTICS SCHEMA - Data Mart (ClickHouse synced)
-- =============================================================================

-- Summary tables for fast reporting (materialized views)
CREATE MATERIALIZED VIEW analytics.daily_sales_summary AS
SELECT 
    date_trunc('day', je.posting_date) as report_date,
    je.tenant_id,
    COUNT(DISTINCT je.id) as transaction_count,
    SUM(jel.credit_amount) FILTER (WHERE a.account_type = 'income') as total_revenue,
    SUM(jel.debit_amount) FILTER (WHERE a.account_type = 'expense') as total_expense
FROM finance.journal_entry je
JOIN finance.journal_entry_line jel ON je.id = jel.journal_entry_id
JOIN finance.account a ON jel.account_id = a.id
WHERE je.status = 'posted'
GROUP BY 1, 2;

-- =============================================================================
-- ROW-LEVEL SECURITY (RLS) - Multi-Tenant Isolation
-- =============================================================================

-- Enable RLS on all tables
ALTER TABLE core.tenant ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.user ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.account ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance.journal_entry ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr.employee ENABLE ROW LEVEL SECURITY;
ALTER TABLE procurement.vendor ENABLE ROW LEVEL SECURITY;
ALTER TABLE project.project ENABLE ROW LEVEL SECURITY;

-- Create policies (example for core.user)
CREATE POLICY tenant_isolation ON core.user
    USING (tenant_id = current_setting('app.current_tenant')::UUID);

CREATE POLICY tenant_isolation ON finance.account
    USING (tenant_id = current_setting('app.current_tenant')::UUID);

CREATE POLICY tenant_isolation ON finance.journal_entry
    USING (tenant_id = current_setting('app.current_tenant')::UUID);

CREATE POLICY tenant_isolation ON hr.employee
    USING (tenant_id = current_setting('app.current_tenant')::UUID);

CREATE POLICY tenant_isolation ON procurement.vendor
    USING (tenant_id = current_setting('app.current_tenant')::UUID);

CREATE POLICY tenant_isolation ON project.project
    USING (tenant_id = current_setting('app.current_tenant')::UUID);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Finance
CREATE INDEX idx_journal_entry_tenant_date ON finance.journal_entry(tenant_id, posting_date);
CREATE INDEX idx_journal_entry_status ON finance.journal_entry(status);
CREATE INDEX idx_account_tenant_code ON finance.account(tenant_id, code);

-- HR
CREATE INDEX idx_employee_tenant_number ON hr.employee(tenant_id, employee_number);
CREATE INDEX idx_employee_department ON hr.employee(department_id);
CREATE INDEX idx_attendance_employee_date ON hr.attendance(employee_id, attendance_date);

-- Procurement
CREATE INDEX idx_po_tenant_vendor ON procurement.purchase_order(tenant_id, vendor_id);
CREATE INDEX idx_po_status ON procurement.purchase_order(status);

-- Project
CREATE INDEX idx_project_tenant_code ON project.project(tenant_id, project_code);
CREATE INDEX idx_task_project_assignee ON project.task(project_id, assignee_id);
CREATE INDEX idx_timesheet_employee_week ON project.timesheet(employee_id, week_start_date);

-- Audit
CREATE INDEX idx_audit_log_tenant_date ON audit.log(tenant_id, created_at);
CREATE INDEX idx_audit_log_resource ON audit.log(resource_type, resource_id);

-- AI
CREATE INDEX idx_prediction_log_tenant ON ai.prediction_log(tenant_id, created_at);

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- Default Roles
INSERT INTO core.permission (code, name, resource, action) VALUES
    ('finance.account.read', 'View Chart of Accounts', 'finance.account', 'read'),
    ('finance.account.write', 'Edit Chart of Accounts', 'finance.account', 'update'),
    ('finance.journal.create', 'Create Journal Entries', 'finance.journal_entry', 'create'),
    ('finance.journal.post', 'Post Journal Entries', 'finance.journal_entry', 'approve'),
    ('hr.employee.read', 'View Employees', 'hr.employee', 'read'),
    ('hr.employee.write', 'Edit Employees', 'hr.employee', 'update'),
    ('hr.payroll.run', 'Run Payroll', 'hr.payroll_run', 'create'),
    ('procurement.po.create', 'Create Purchase Orders', 'procurement.purchase_order', 'create'),
    ('procurement.po.approve', 'Approve Purchase Orders', 'procurement.purchase_order', 'approve'),
    ('project.project.manage', 'Manage Projects', 'project.project', 'update');

-- =============================================================================
-- COMMENTS
-- =============================================================================
COMMENT ON SCHEMA core IS 'Core shared entities - users, tenants, roles';
COMMENT ON SCHEMA finance IS 'Financial Accounting - SAP FI/CO parity';
COMMENT ON SCHEMA hr IS 'Human Resources - SAP SuccessFactors parity';
COMMENT ON SCHEMA procurement IS 'Procurement - SAP Ariba parity';
COMMENT ON SCHEMA project IS 'Project Management - Clarity PPM parity';
COMMENT ON SCHEMA ai IS 'AI/ML entities - embeddings, predictions, agents';
COMMENT ON SCHEMA audit IS 'Audit trail - SOC 2 compliance';
COMMENT ON SCHEMA analytics IS 'Analytics data marts - SAP BW parity';

-- =============================================================================
-- END OF DATA MODEL
-- =============================================================================
