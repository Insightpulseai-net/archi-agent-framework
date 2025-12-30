# -*- coding: utf-8 -*-
"""SSS Contribution Table for 2024."""

from odoo import models, fields, api


class SSSContribution(models.Model):
    """SSS Contribution Table 2024."""

    _name = 'bir.sss.contribution'
    _description = 'SSS Contribution Table'
    _order = 'salary_from'

    name = fields.Char(
        string='Bracket Name',
        compute='_compute_name',
        store=True,
    )
    salary_from = fields.Float(
        string='Salary From',
        required=True,
    )
    salary_to = fields.Float(
        string='Salary To',
        required=True,
    )
    monthly_salary_credit = fields.Float(
        string='Monthly Salary Credit',
        required=True,
    )
    employee_share = fields.Float(
        string='Employee Share (EE)',
        required=True,
        help='Employee contribution',
    )
    employer_share = fields.Float(
        string='Employer Share (ER)',
        required=True,
        help='Employer contribution',
    )
    total_contribution = fields.Float(
        string='Total Contribution',
        compute='_compute_total',
        store=True,
    )
    ec_contribution = fields.Float(
        string='EC Contribution',
        default=10.00,
        help='Employees Compensation (paid by employer)',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    year = fields.Integer(
        string='Effective Year',
        default=2024,
    )

    @api.depends('salary_from', 'salary_to')
    def _compute_name(self):
        for record in self:
            record.name = f"₱{record.salary_from:,.0f} - ₱{record.salary_to:,.0f}"

    @api.depends('employee_share', 'employer_share')
    def _compute_total(self):
        for record in self:
            record.total_contribution = (
                record.employee_share + record.employer_share
            )

    @api.model
    def get_contribution(self, salary):
        """Get SSS contribution for a given salary."""
        line = self.search([
            ('salary_from', '<=', salary),
            ('salary_to', '>=', salary),
            ('active', '=', True),
        ], limit=1)

        if line:
            return {
                'employee_share': line.employee_share,
                'employer_share': line.employer_share,
                'total': line.total_contribution,
                'ec': line.ec_contribution,
            }
        else:
            # Return max contribution
            max_line = self.search(
                [('active', '=', True)],
                order='salary_to desc',
                limit=1
            )
            if max_line:
                return {
                    'employee_share': max_line.employee_share,
                    'employer_share': max_line.employer_share,
                    'total': max_line.total_contribution,
                    'ec': max_line.ec_contribution,
                }
            return {
                'employee_share': 1350.00,
                'employer_share': 1350.00,
                'total': 2700.00,
                'ec': 10.00,
            }
