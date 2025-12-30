# -*- coding: utf-8 -*-
"""BIR Form model for generating and tracking tax forms."""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
from datetime import date, timedelta
import json

_logger = logging.getLogger(__name__)


class BIRForm(models.Model):
    """BIR Form - Individual form instances for filing."""

    _name = 'bir.form'
    _description = 'BIR Form'
    _order = 'period_end desc, form_type_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default='/',
    )
    form_type_id = fields.Many2one(
        'bir.form.type',
        string='Form Type',
        required=True,
        ondelete='restrict',
    )
    form_code = fields.Char(
        related='form_type_id.code',
        store=True,
    )
    category = fields.Selection(
        related='form_type_id.category',
        store=True,
    )

    # Period
    period_start = fields.Date(
        string='Period Start',
        required=True,
    )
    period_end = fields.Date(
        string='Period End',
        required=True,
    )
    due_date = fields.Date(
        string='Due Date',
        compute='_compute_due_date',
        store=True,
    )
    filing_date = fields.Date(
        string='Filing Date',
    )

    # State
    state = fields.Selection([
        ('draft', 'Draft'),
        ('computed', 'Computed'),
        ('validated', 'Validated'),
        ('submitted', 'Submitted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('amended', 'Amended'),
    ], string='State', default='draft', tracking=True)

    # Taxpayer Info
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
    )
    tin = fields.Char(
        string='TIN',
        compute='_compute_tin',
        store=True,
    )
    registered_name = fields.Char(
        string='Registered Name',
        compute='_compute_tin',
        store=True,
    )
    rdo_code = fields.Char(
        string='RDO Code',
    )

    # Amounts (generic, form-specific fields in form_data)
    gross_amount = fields.Float(
        string='Gross Amount',
    )
    taxable_amount = fields.Float(
        string='Taxable Amount',
    )
    tax_due = fields.Float(
        string='Tax Due',
    )
    tax_credits = fields.Float(
        string='Tax Credits',
    )
    tax_payable = fields.Float(
        string='Tax Payable',
        compute='_compute_tax_payable',
        store=True,
    )
    penalties = fields.Float(
        string='Penalties',
    )
    total_amount_due = fields.Float(
        string='Total Amount Due',
        compute='_compute_total_due',
        store=True,
    )

    # Form-specific data (JSON)
    form_data = fields.Text(
        string='Form Data (JSON)',
        help='Form-specific fields stored as JSON',
    )
    form_data_display = fields.Text(
        string='Form Data Display',
        compute='_compute_form_data_display',
    )

    # Attachments
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Attachments',
    )

    # E-Filing
    confirmation_number = fields.Char(
        string='Confirmation Number',
        readonly=True,
    )
    filing_reference = fields.Char(
        string='Filing Reference',
        readonly=True,
    )
    submission_log = fields.Text(
        string='Submission Log',
        readonly=True,
    )

    # Related records
    calculation_ids = fields.Many2many(
        'bir.tax.calculation',
        string='Related Calculations',
    )
    filing_id = fields.Many2one(
        'bir.filing',
        string='Filing Batch',
        ondelete='set null',
    )

    # Amendment tracking
    is_amendment = fields.Boolean(
        string='Is Amendment',
        default=False,
    )
    original_form_id = fields.Many2one(
        'bir.form',
        string='Original Form',
        ondelete='set null',
    )
    amendment_reason = fields.Text(
        string='Amendment Reason',
    )

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('bir.form') or '/'
        return super().create(vals)

    @api.depends('company_id')
    def _compute_tin(self):
        for record in self:
            if record.company_id:
                record.tin = record.company_id.vat or ''
                record.registered_name = record.company_id.name
            else:
                record.tin = ''
                record.registered_name = ''

    @api.depends('period_end', 'form_type_id')
    def _compute_due_date(self):
        for record in self:
            if not record.period_end or not record.form_type_id:
                record.due_date = False
                continue

            form_type = record.form_type_id
            period_end = record.period_end

            if form_type.deadline_offset == 'following_month':
                # Next month + deadline_day
                next_month = period_end.replace(day=1) + timedelta(days=32)
                due_day = min(form_type.deadline_day or 10, 28)
                record.due_date = next_month.replace(day=due_day)

            elif form_type.deadline_offset == 'following_quarter':
                # 25th of month following quarter end
                quarter_month = ((period_end.month - 1) // 3 + 1) * 3
                next_month = period_end.replace(month=quarter_month, day=1) + timedelta(days=32)
                record.due_date = next_month.replace(day=25)

            elif form_type.deadline_offset == 'following_year':
                # April 15 of following year
                record.due_date = date(period_end.year + 1, 4, 15)

            else:
                # Default: 30 days after period end
                record.due_date = period_end + timedelta(days=30)

    @api.depends('tax_due', 'tax_credits')
    def _compute_tax_payable(self):
        for record in self:
            record.tax_payable = max(record.tax_due - record.tax_credits, 0)

    @api.depends('tax_payable', 'penalties')
    def _compute_total_due(self):
        for record in self:
            record.total_amount_due = record.tax_payable + record.penalties

    @api.depends('form_data')
    def _compute_form_data_display(self):
        for record in self:
            if record.form_data:
                try:
                    data = json.loads(record.form_data)
                    record.form_data_display = json.dumps(data, indent=2)
                except json.JSONDecodeError:
                    record.form_data_display = record.form_data
            else:
                record.form_data_display = ''

    def action_compute(self):
        """Compute form values based on related records."""
        for record in self:
            if record.form_code == '1601-C':
                self._compute_1601c(record)
            elif record.form_code == '2550-Q':
                self._compute_2550q(record)
            elif record.form_code == '1700':
                self._compute_1700(record)
            # Add more form-specific computations

            record.state = 'computed'
        return True

    def _compute_1601c(self, record):
        """Compute BIR Form 1601-C (Monthly Withholding Tax)."""
        # Get all tax calculations for the period
        calculations = self.env['bir.tax.calculation'].search([
            ('calculation_date', '>=', record.period_start),
            ('calculation_date', '<=', record.period_end),
            ('state', 'in', ['calculated', 'validated']),
        ])

        total_compensation = sum(calculations.mapped('total_taxable_income'))
        total_tax = sum(calculations.mapped('withholding_tax'))

        record.gross_amount = total_compensation
        record.taxable_amount = total_compensation
        record.tax_due = total_tax
        record.calculation_ids = [(6, 0, calculations.ids)]

        # Store form-specific data
        record.form_data = json.dumps({
            'total_compensation_income': total_compensation,
            'tax_withheld': total_tax,
            'employee_count': len(calculations),
            'period_month': record.period_end.month,
            'period_year': record.period_end.year,
        })

    def _compute_2550q(self, record):
        """Compute BIR Form 2550-Q (Quarterly VAT)."""
        # Get invoices for the period
        invoices = self.env['account.move'].search([
            ('invoice_date', '>=', record.period_start),
            ('invoice_date', '<=', record.period_end),
            ('state', '=', 'posted'),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('company_id', '=', record.company_id.id),
        ])

        total_sales = sum(invoices.mapped('amount_untaxed'))
        output_vat = total_sales * 0.12  # 12% VAT

        # Get purchases for input VAT
        bills = self.env['account.move'].search([
            ('invoice_date', '>=', record.period_start),
            ('invoice_date', '<=', record.period_end),
            ('state', '=', 'posted'),
            ('move_type', 'in', ['in_invoice', 'in_refund']),
            ('company_id', '=', record.company_id.id),
        ])

        total_purchases = sum(bills.mapped('amount_untaxed'))
        input_vat = total_purchases * 0.12

        record.gross_amount = total_sales
        record.taxable_amount = total_sales
        record.tax_due = output_vat
        record.tax_credits = input_vat

        record.form_data = json.dumps({
            'total_sales': total_sales,
            'output_vat': output_vat,
            'total_purchases': total_purchases,
            'input_vat': input_vat,
            'net_vat_payable': output_vat - input_vat,
            'quarter': (record.period_end.month - 1) // 3 + 1,
            'year': record.period_end.year,
        })

    def _compute_1700(self, record):
        """Compute BIR Form 1700 (Annual Income Tax - Individual)."""
        # Annual computation
        calculations = self.env['bir.tax.calculation'].search([
            ('calculation_date', '>=', record.period_start),
            ('calculation_date', '<=', record.period_end),
            ('state', 'in', ['calculated', 'validated']),
        ])

        total_income = sum(calculations.mapped('total_taxable_income'))
        total_deductions = sum(calculations.mapped('total_mandatory_deductions'))
        total_tax = sum(calculations.mapped('withholding_tax'))

        record.gross_amount = total_income
        record.taxable_amount = total_income - total_deductions
        record.tax_due = total_tax
        record.tax_credits = total_tax  # Assuming withheld = credits

        record.form_data = json.dumps({
            'gross_compensation_income': total_income,
            'total_deductions': total_deductions,
            'taxable_income': total_income - total_deductions,
            'tax_due': total_tax,
            'tax_withheld': total_tax,
            'tax_payable': 0,  # Should be zero if properly withheld
            'year': record.period_end.year,
        })

    def action_validate(self):
        """Validate form for submission."""
        for record in self:
            if record.state != 'computed':
                raise ValidationError(_('Please compute the form first.'))

            # Run validation checks
            errors = []

            if not record.tin:
                errors.append(_('TIN is required.'))
            if record.tax_payable < 0:
                errors.append(_('Tax payable cannot be negative.'))
            if not record.period_start or not record.period_end:
                errors.append(_('Period dates are required.'))

            if errors:
                raise ValidationError('\n'.join(errors))

            record.state = 'validated'
        return True

    def action_submit(self):
        """Submit form to BIR (placeholder for e-filing integration)."""
        for record in self:
            if record.state != 'validated':
                raise ValidationError(_('Please validate the form first.'))

            # TODO: Integrate with BIR e-filing API
            # For now, just update state and log
            record.state = 'submitted'
            record.filing_date = fields.Date.today()
            record.confirmation_number = f"IPAI-{record.name}-{fields.Date.today().strftime('%Y%m%d')}"
            record.submission_log = (
                f"Submitted on {fields.Datetime.now()}\n"
                f"Form: {record.form_code}\n"
                f"Period: {record.period_start} to {record.period_end}\n"
                f"Amount Due: ₱{record.total_amount_due:,.2f}\n"
            )
        return True

    def action_reset_draft(self):
        """Reset to draft state."""
        for record in self:
            if record.state in ['accepted']:
                raise ValidationError(_('Cannot reset accepted forms.'))
            record.state = 'draft'
        return True

    def action_create_amendment(self):
        """Create an amendment for this form."""
        self.ensure_one()
        if self.state not in ['accepted', 'submitted']:
            raise ValidationError(_('Can only amend submitted or accepted forms.'))

        amendment = self.copy({
            'is_amendment': True,
            'original_form_id': self.id,
            'state': 'draft',
            'confirmation_number': False,
            'filing_reference': False,
            'filing_date': False,
        })

        self.state = 'amended'

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'bir.form',
            'res_id': amendment.id,
            'view_mode': 'form',
        }
