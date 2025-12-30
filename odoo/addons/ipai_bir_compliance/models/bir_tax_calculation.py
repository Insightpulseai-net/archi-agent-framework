# -*- coding: utf-8 -*-
"""BIR Tax Calculation Model for Odoo 18 CE.

This module implements Philippine tax calculations including:
- SSS contributions (2024 table)
- PhilHealth (2.5% employee share, max ₱1,250)
- PAGIBIG (2% employee share, max ₱100)
- Withholding tax (graduated rates per TRAIN Law)
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
from decimal import Decimal, ROUND_HALF_UP

_logger = logging.getLogger(__name__)


class BIRTaxCalculation(models.Model):
    """BIR Tax Calculation for payroll and invoices."""

    _name = 'bir.tax.calculation'
    _description = 'BIR Tax Calculation'
    _order = 'create_date desc'
    _rec_name = 'display_name'

    # --- Identification ---
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
        index=True,
    )
    payroll_period = fields.Many2one(
        'hr.payslip.run',
        string='Payroll Period',
        ondelete='set null',
    )
    calculation_date = fields.Date(
        string='Calculation Date',
        default=fields.Date.context_today,
        required=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('validated', 'Validated'),
        ('filed', 'Filed'),
    ], string='State', default='draft', tracking=True)

    # --- Income ---
    gross_salary = fields.Float(
        string='Gross Salary',
        required=True,
        help='Monthly gross salary in PHP',
    )
    overtime_pay = fields.Float(
        string='Overtime Pay',
        default=0.0,
    )
    holiday_pay = fields.Float(
        string='Holiday Pay',
        default=0.0,
    )
    night_differential = fields.Float(
        string='Night Differential',
        default=0.0,
    )
    other_taxable_income = fields.Float(
        string='Other Taxable Income',
        default=0.0,
    )
    total_taxable_income = fields.Float(
        string='Total Taxable Income',
        compute='_compute_total_taxable_income',
        store=True,
    )

    # --- Non-Taxable Income ---
    thirteenth_month_pay = fields.Float(
        string='13th Month Pay',
        default=0.0,
        help='Non-taxable if ≤ ₱90,000',
    )
    de_minimis_benefits = fields.Float(
        string='De Minimis Benefits',
        default=0.0,
    )

    # --- Mandatory Deductions ---
    sss_contribution = fields.Float(
        string='SSS Contribution',
        compute='_compute_sss',
        store=True,
        help='Based on SSS Contribution Table 2024',
    )
    philhealth = fields.Float(
        string='PhilHealth',
        compute='_compute_philhealth',
        store=True,
        help='2.5% employee share, max ₱1,250',
    )
    pagibig = fields.Float(
        string='PAGIBIG',
        compute='_compute_pagibig',
        store=True,
        help='2% employee share, max ₱100',
    )
    total_mandatory_deductions = fields.Float(
        string='Total Mandatory Deductions',
        compute='_compute_total_mandatory',
        store=True,
    )

    # --- Withholding Tax ---
    taxable_income_after_deductions = fields.Float(
        string='Taxable Income After Deductions',
        compute='_compute_taxable_after_deductions',
        store=True,
    )
    withholding_tax = fields.Float(
        string='Withholding Tax',
        compute='_compute_withholding_tax',
        store=True,
        help='Based on 2024 graduated tax rates',
    )
    tax_bracket = fields.Char(
        string='Tax Bracket',
        compute='_compute_withholding_tax',
        store=True,
    )

    # --- Net Pay ---
    total_deductions = fields.Float(
        string='Total Deductions',
        compute='_compute_total_deductions',
        store=True,
    )
    net_salary = fields.Float(
        string='Net Salary',
        compute='_compute_net_salary',
        store=True,
    )

    # --- Exemptions ---
    is_minimum_wage_earner = fields.Boolean(
        string='Minimum Wage Earner',
        help='Exempt from withholding tax',
    )
    is_senior_citizen = fields.Boolean(
        string='Senior Citizen',
        help='Additional ₱25,000 exemption',
    )
    is_pwd = fields.Boolean(
        string='Person with Disability',
        help='Additional ₱25,000 exemption',
    )

    # --- Audit Trail ---
    notes = fields.Text(string='Notes')
    calculation_log = fields.Text(
        string='Calculation Log',
        readonly=True,
    )

    @api.depends('employee_id', 'calculation_date')
    def _compute_display_name(self):
        for record in self:
            if record.employee_id and record.calculation_date:
                record.display_name = f"{record.employee_id.name} - {record.calculation_date}"
            else:
                record.display_name = _('New Calculation')

    @api.depends('gross_salary', 'overtime_pay', 'holiday_pay',
                 'night_differential', 'other_taxable_income')
    def _compute_total_taxable_income(self):
        for record in self:
            record.total_taxable_income = (
                record.gross_salary +
                record.overtime_pay +
                record.holiday_pay +
                record.night_differential +
                record.other_taxable_income
            )

    @api.depends('gross_salary')
    def _compute_sss(self):
        """Compute SSS contribution based on 2024 table."""
        for record in self:
            # Get SSS contribution from table
            sss_line = self.env['bir.sss.contribution'].search([
                ('salary_from', '<=', record.gross_salary),
                ('salary_to', '>=', record.gross_salary),
            ], limit=1)

            if sss_line:
                record.sss_contribution = sss_line.employee_share
            else:
                # Fallback to max contribution
                max_sss = self.env['bir.sss.contribution'].search(
                    [], order='salary_to desc', limit=1
                )
                record.sss_contribution = max_sss.employee_share if max_sss else 1350.00

            _logger.info(
                f"SSS computed for {record.employee_id.name}: "
                f"gross={record.gross_salary}, sss={record.sss_contribution}"
            )

    @api.depends('gross_salary')
    def _compute_philhealth(self):
        """Compute PhilHealth: 2.5% employee share, max ₱1,250."""
        for record in self:
            # 5% total, split equally (2.5% employee, 2.5% employer)
            contribution = record.gross_salary * 0.025
            record.philhealth = min(contribution, 1250.00)

    @api.depends('gross_salary')
    def _compute_pagibig(self):
        """Compute PAGIBIG: 2% employee share, max ₱100."""
        for record in self:
            if record.gross_salary <= 1500:
                # 1% for salary ≤ ₱1,500
                contribution = record.gross_salary * 0.01
            else:
                # 2% for salary > ₱1,500
                contribution = record.gross_salary * 0.02
            record.pagibig = min(contribution, 100.00)

    @api.depends('sss_contribution', 'philhealth', 'pagibig')
    def _compute_total_mandatory(self):
        for record in self:
            record.total_mandatory_deductions = (
                record.sss_contribution +
                record.philhealth +
                record.pagibig
            )

    @api.depends('total_taxable_income', 'total_mandatory_deductions',
                 'is_senior_citizen', 'is_pwd')
    def _compute_taxable_after_deductions(self):
        for record in self:
            taxable = record.total_taxable_income - record.total_mandatory_deductions

            # Apply exemptions
            if record.is_senior_citizen:
                taxable -= 25000 / 12  # Monthly equivalent
            if record.is_pwd:
                taxable -= 25000 / 12  # Monthly equivalent

            record.taxable_income_after_deductions = max(taxable, 0)

    @api.depends('taxable_income_after_deductions', 'is_minimum_wage_earner')
    def _compute_withholding_tax(self):
        """Compute withholding tax based on 2024 graduated rates (TRAIN Law)."""
        for record in self:
            if record.is_minimum_wage_earner:
                record.withholding_tax = 0.0
                record.tax_bracket = 'EXEMPT (MWE)'
                continue

            # Annualize for tax bracket calculation
            annual_taxable = record.taxable_income_after_deductions * 12

            # 2024 Tax Brackets (TRAIN Law)
            if annual_taxable <= 250000:
                annual_tax = 0
                bracket = '0% (≤₱250K)'
            elif annual_taxable <= 400000:
                annual_tax = (annual_taxable - 250000) * 0.15
                bracket = '15% (₱250K-₱400K)'
            elif annual_taxable <= 800000:
                annual_tax = 22500 + (annual_taxable - 400000) * 0.20
                bracket = '20% (₱400K-₱800K)'
            elif annual_taxable <= 2000000:
                annual_tax = 102500 + (annual_taxable - 800000) * 0.25
                bracket = '25% (₱800K-₱2M)'
            elif annual_taxable <= 8000000:
                annual_tax = 402500 + (annual_taxable - 2000000) * 0.30
                bracket = '30% (₱2M-₱8M)'
            else:
                annual_tax = 2202500 + (annual_taxable - 8000000) * 0.35
                bracket = '35% (>₱8M)'

            record.withholding_tax = annual_tax / 12
            record.tax_bracket = bracket

    @api.depends('total_mandatory_deductions', 'withholding_tax')
    def _compute_total_deductions(self):
        for record in self:
            record.total_deductions = (
                record.total_mandatory_deductions +
                record.withholding_tax
            )

    @api.depends('total_taxable_income', 'total_deductions')
    def _compute_net_salary(self):
        for record in self:
            record.net_salary = (
                record.total_taxable_income -
                record.total_deductions
            )

    @api.constrains('gross_salary')
    def _check_gross_salary(self):
        """Validate gross salary is non-negative."""
        for record in self:
            if record.gross_salary < 0:
                raise ValidationError(
                    _('Gross salary cannot be negative.')
                )

    def action_calculate(self):
        """Trigger calculation and move to calculated state."""
        for record in self:
            # Calculations are done via computed fields
            # Just update state and log
            record.state = 'calculated'
            record.calculation_log = (
                f"Calculated on {fields.Datetime.now()}\n"
                f"Gross: ₱{record.gross_salary:,.2f}\n"
                f"SSS: ₱{record.sss_contribution:,.2f}\n"
                f"PhilHealth: ₱{record.philhealth:,.2f}\n"
                f"PAGIBIG: ₱{record.pagibig:,.2f}\n"
                f"Tax: ₱{record.withholding_tax:,.2f} ({record.tax_bracket})\n"
                f"Net: ₱{record.net_salary:,.2f}"
            )
        return True

    def action_validate(self):
        """Validate calculation for filing."""
        for record in self:
            if record.state != 'calculated':
                raise ValidationError(_('Please calculate first.'))
            record.state = 'validated'
        return True

    def action_reset_draft(self):
        """Reset to draft state."""
        for record in self:
            record.state = 'draft'
        return True
