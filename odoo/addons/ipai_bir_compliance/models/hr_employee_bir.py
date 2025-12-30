# -*- coding: utf-8 -*-
"""Extension of hr.employee for BIR compliance fields."""

from odoo import models, fields


class HrEmployeeBIR(models.Model):
    """Extend hr.employee with BIR compliance fields."""

    _inherit = 'hr.employee'

    # TIN
    bir_tin = fields.Char(
        string='TIN',
        help='Taxpayer Identification Number',
    )
    bir_tin_branch = fields.Char(
        string='TIN Branch Code',
        default='000',
    )

    # Tax Status
    tax_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('head_of_family', 'Head of Family'),
    ], string='Tax Status', default='single')

    # Exemptions
    is_minimum_wage_earner = fields.Boolean(
        string='Minimum Wage Earner',
        help='Exempt from withholding tax',
    )
    is_senior_citizen = fields.Boolean(
        string='Senior Citizen',
        help='Age 60+ years, additional exemption',
    )
    is_pwd = fields.Boolean(
        string='Person with Disability',
        help='Additional exemption',
    )
    pwd_id = fields.Char(
        string='PWD ID Number',
    )

    # Dependents (for additional exemptions)
    dependent_count = fields.Integer(
        string='Number of Dependents',
        default=0,
        help='Number of qualified dependents (max 4)',
    )
    dependent_ids = fields.One2many(
        'hr.employee.dependent',
        'employee_id',
        string='Dependents',
    )

    # Previous Employer (for Form 2316)
    previous_employer_name = fields.Char(
        string='Previous Employer Name',
    )
    previous_employer_tin = fields.Char(
        string='Previous Employer TIN',
    )
    previous_employer_address = fields.Char(
        string='Previous Employer Address',
    )
    previous_employment_start = fields.Date(
        string='Previous Employment Start',
    )
    previous_employment_end = fields.Date(
        string='Previous Employment End',
    )
    previous_gross_compensation = fields.Float(
        string='Previous Gross Compensation',
    )
    previous_tax_withheld = fields.Float(
        string='Previous Tax Withheld',
    )

    # SSS/PhilHealth/PAGIBIG Numbers
    sss_number = fields.Char(
        string='SSS Number',
    )
    philhealth_number = fields.Char(
        string='PhilHealth Number',
    )
    pagibig_number = fields.Char(
        string='PAGIBIG Number',
    )

    # Bank Account for Payroll
    bank_account_id = fields.Many2one(
        'res.partner.bank',
        string='Bank Account',
    )


class HrEmployeeDependent(models.Model):
    """Employee dependents for tax exemption purposes."""

    _name = 'hr.employee.dependent'
    _description = 'Employee Dependent'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
    )
    name = fields.Char(
        string='Name',
        required=True,
    )
    relationship = fields.Selection([
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('parent', 'Parent'),
    ], string='Relationship', required=True)
    birthdate = fields.Date(
        string='Birthdate',
    )
    is_pwd = fields.Boolean(
        string='PWD',
    )
    is_senior = fields.Boolean(
        string='Senior Citizen',
    )
