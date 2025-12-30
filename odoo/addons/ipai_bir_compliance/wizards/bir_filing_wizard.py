# -*- coding: utf-8 -*-
"""BIR Filing Wizard for batch form generation and submission."""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class BIRFilingWizard(models.TransientModel):
    """Wizard for creating BIR filing batches."""

    _name = 'bir.filing.wizard'
    _description = 'BIR Filing Wizard'

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
    )
    period_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
    ], string='Period Type', default='monthly', required=True)

    period_month = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ], string='Month', default=lambda self: str(date.today().month))

    period_quarter = fields.Selection([
        ('1', 'Q1 (Jan-Mar)'),
        ('2', 'Q2 (Apr-Jun)'),
        ('3', 'Q3 (Jul-Sep)'),
        ('4', 'Q4 (Oct-Dec)'),
    ], string='Quarter')

    period_year = fields.Integer(
        string='Year',
        default=lambda self: date.today().year,
        required=True,
    )

    form_type_ids = fields.Many2many(
        'bir.form.type',
        string='Form Types',
        help='Leave empty to include all applicable forms',
    )

    include_1601c = fields.Boolean(
        string='Include 1601-C (Withholding Tax)',
        default=True,
    )
    include_2550m = fields.Boolean(
        string='Include 2550-M (Monthly VAT)',
        default=True,
    )
    include_2550q = fields.Boolean(
        string='Include 2550-Q (Quarterly VAT)',
        default=True,
    )

    @api.onchange('period_type')
    def _onchange_period_type(self):
        if self.period_type == 'monthly':
            self.period_quarter = False
        elif self.period_type == 'quarterly':
            current_quarter = (date.today().month - 1) // 3 + 1
            self.period_quarter = str(current_quarter)

    def _get_period_dates(self):
        """Calculate period start and end dates."""
        year = self.period_year

        if self.period_type == 'monthly':
            month = int(self.period_month)
            start = date(year, month, 1)
            if month == 12:
                end = date(year, 12, 31)
            else:
                end = date(year, month + 1, 1).replace(day=1)
                end = end.replace(day=1) - timedelta(days=1)
                # Simpler: last day of month
                import calendar
                last_day = calendar.monthrange(year, month)[1]
                end = date(year, month, last_day)

        elif self.period_type == 'quarterly':
            quarter = int(self.period_quarter)
            start_month = (quarter - 1) * 3 + 1
            end_month = quarter * 3
            start = date(year, start_month, 1)
            import calendar
            last_day = calendar.monthrange(year, end_month)[1]
            end = date(year, end_month, last_day)

        else:  # annual
            start = date(year, 1, 1)
            end = date(year, 12, 31)

        return start, end

    def action_create_filing(self):
        """Create filing batch with forms."""
        self.ensure_one()

        import calendar
        year = self.period_year

        if self.period_type == 'monthly':
            month = int(self.period_month)
            start = date(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            end = date(year, month, last_day)
        elif self.period_type == 'quarterly':
            quarter = int(self.period_quarter)
            start_month = (quarter - 1) * 3 + 1
            end_month = quarter * 3
            start = date(year, start_month, 1)
            last_day = calendar.monthrange(year, end_month)[1]
            end = date(year, end_month, last_day)
        else:
            start = date(year, 1, 1)
            end = date(year, 12, 31)

        # Create filing batch
        filing = self.env['bir.filing'].create({
            'company_id': self.company_id.id,
            'period_start': start,
            'period_end': end,
        })

        # Generate forms
        filing.action_generate_forms()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'bir.filing',
            'res_id': filing.id,
            'view_mode': 'form',
            'target': 'current',
        }
