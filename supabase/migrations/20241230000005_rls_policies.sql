-- Migration: 20241230000005_rls_policies.sql
-- Description: Create Row Level Security policies for all tables
-- Author: InsightPulseAI

-- =====================================================
-- Enable RLS on Silver Tables
-- =====================================================

ALTER TABLE silver.partners ENABLE ROW LEVEL SECURITY;
ALTER TABLE silver.employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE silver.invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE silver.payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE silver.payslips ENABLE ROW LEVEL SECURITY;
ALTER TABLE silver.bir_forms ENABLE ROW LEVEL SECURITY;
ALTER TABLE silver.audit_log ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- Helper Function: Get User Role
-- =====================================================

CREATE OR REPLACE FUNCTION auth.get_user_role()
RETURNS TEXT AS $$
BEGIN
    RETURN COALESCE(
        current_setting('request.jwt.claims', true)::json->>'role',
        'employee'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- Partners: Read by all authenticated, write by admins
-- =====================================================

-- Read: All authenticated users can read partners
CREATE POLICY partners_read_all
ON silver.partners FOR SELECT
TO authenticated
USING (true);

-- Write: Only admins and managers can modify
CREATE POLICY partners_write_admin
ON silver.partners FOR ALL
TO authenticated
USING (auth.get_user_role() IN ('admin', 'manager'))
WITH CHECK (auth.get_user_role() IN ('admin', 'manager'));

-- =====================================================
-- Employees: Read own or if manager, write by HR/admin
-- =====================================================

-- Read: Employees can see themselves, managers can see their team
CREATE POLICY employees_read_self
ON silver.employees FOR SELECT
TO authenticated
USING (
    user_id = auth.uid()
    OR auth.get_user_role() IN ('admin', 'hr_manager', 'manager')
);

-- Write: Only HR and admin can modify
CREATE POLICY employees_write_hr
ON silver.employees FOR ALL
TO authenticated
USING (auth.get_user_role() IN ('admin', 'hr_manager'))
WITH CHECK (auth.get_user_role() IN ('admin', 'hr_manager'));

-- =====================================================
-- Invoices: Role-based access
-- =====================================================

-- Admin/Manager: Full access
CREATE POLICY invoices_admin_full
ON silver.invoices FOR ALL
TO authenticated
USING (auth.get_user_role() IN ('admin', 'manager', 'finance_manager'))
WITH CHECK (auth.get_user_role() IN ('admin', 'manager', 'finance_manager'));

-- Approver: Can view and update pending invoices
CREATE POLICY invoices_approver_pending
ON silver.invoices FOR SELECT
TO authenticated
USING (
    auth.get_user_role() = 'approver'
    AND approval_state = 'pending'
);

CREATE POLICY invoices_approver_update
ON silver.invoices FOR UPDATE
TO authenticated
USING (
    auth.get_user_role() = 'approver'
    AND approval_state = 'pending'
)
WITH CHECK (
    approval_state IN ('approved', 'rejected')
);

-- Analyst: Read-only access
CREATE POLICY invoices_analyst_read
ON silver.invoices FOR SELECT
TO authenticated
USING (auth.get_user_role() = 'analyst');

-- Employee: Own invoices only (if linked to partner)
CREATE POLICY invoices_employee_own
ON silver.invoices FOR SELECT
TO authenticated
USING (
    auth.get_user_role() = 'employee'
    AND partner_id IN (
        SELECT odoo_id FROM silver.partners
        WHERE email = (SELECT email FROM auth.users WHERE id = auth.uid())
    )
);

-- =====================================================
-- Payments: Similar to invoices
-- =====================================================

CREATE POLICY payments_admin_full
ON silver.payments FOR ALL
TO authenticated
USING (auth.get_user_role() IN ('admin', 'manager', 'finance_manager'))
WITH CHECK (auth.get_user_role() IN ('admin', 'manager', 'finance_manager'));

CREATE POLICY payments_approver_pending
ON silver.payments FOR SELECT
TO authenticated
USING (
    auth.get_user_role() = 'approver'
    AND approval_state = 'pending'
);

CREATE POLICY payments_analyst_read
ON silver.payments FOR SELECT
TO authenticated
USING (auth.get_user_role() = 'analyst');

-- =====================================================
-- Payslips: Employees see own, HR sees all
-- =====================================================

-- Admin/HR: Full access
CREATE POLICY payslips_hr_full
ON silver.payslips FOR ALL
TO authenticated
USING (auth.get_user_role() IN ('admin', 'hr_manager', 'payroll_officer'))
WITH CHECK (auth.get_user_role() IN ('admin', 'hr_manager', 'payroll_officer'));

-- Employees: View own payslips only
CREATE POLICY payslips_employee_own
ON silver.payslips FOR SELECT
TO authenticated
USING (
    employee_id IN (
        SELECT odoo_id FROM silver.employees
        WHERE user_id = auth.uid()
    )
);

-- Managers: View team payslips
CREATE POLICY payslips_manager_team
ON silver.payslips FOR SELECT
TO authenticated
USING (
    auth.get_user_role() = 'manager'
    AND employee_id IN (
        SELECT odoo_id FROM silver.employees
        WHERE manager_id IN (
            SELECT odoo_id FROM silver.employees WHERE user_id = auth.uid()
        )
    )
);

-- =====================================================
-- BIR Forms: Finance and admin only
-- =====================================================

CREATE POLICY bir_forms_finance_full
ON silver.bir_forms FOR ALL
TO authenticated
USING (auth.get_user_role() IN ('admin', 'finance_manager', 'tax_officer'))
WITH CHECK (auth.get_user_role() IN ('admin', 'finance_manager', 'tax_officer'));

-- Analyst: Read-only
CREATE POLICY bir_forms_analyst_read
ON silver.bir_forms FOR SELECT
TO authenticated
USING (auth.get_user_role() = 'analyst');

-- =====================================================
-- Audit Log: Immutable, read by admin only
-- =====================================================

CREATE POLICY audit_log_admin_read
ON silver.audit_log FOR SELECT
TO authenticated
USING (auth.get_user_role() IN ('admin', 'auditor'));

-- No insert/update/delete policies = immutable
-- Use service_role for writing audit logs

-- =====================================================
-- Grant Permissions
-- =====================================================

-- Grant SELECT on all silver tables to authenticated
GRANT SELECT ON ALL TABLES IN SCHEMA silver TO authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA gold TO authenticated;

-- Grant INSERT/UPDATE to authenticated (RLS will filter)
GRANT INSERT, UPDATE ON silver.invoices TO authenticated;
GRANT INSERT, UPDATE ON silver.payments TO authenticated;
GRANT INSERT, UPDATE ON silver.payslips TO authenticated;
GRANT INSERT, UPDATE ON silver.bir_forms TO authenticated;

-- Service role gets full access (for backend operations)
GRANT ALL ON ALL TABLES IN SCHEMA bronze TO service_role;
GRANT ALL ON ALL TABLES IN SCHEMA silver TO service_role;
GRANT ALL ON ALL TABLES IN SCHEMA gold TO service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA bronze TO service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA silver TO service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA gold TO service_role;
