# -*- coding: utf-8 -*-
"""BIR Filing batch for bulk form submission."""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class BIRFiling(models.Model):
    """BIR Filing - Batch submission of multiple forms."""

    _name = 'bir.filing'
    _description = 'BIR Filing Batch'
    _order = 'filing_date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default='/',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
    )
    filing_date = fields.Date(
        string='Filing Date',
        default=fields.Date.context_today,
        required=True,
    )
    period_start = fields.Date(
        string='Period Start',
        required=True,
    )
    period_end = fields.Date(
        string='Period End',
        required=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('submitted', 'Submitted'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], string='State', default='draft', tracking=True)

    # Forms
    form_ids = fields.One2many(
        'bir.form',
        'filing_id',
        string='Forms',
    )
    form_count = fields.Integer(
        string='Form Count',
        compute='_compute_counts',
    )
    submitted_count = fields.Integer(
        string='Submitted Count',
        compute='_compute_counts',
    )
    failed_count = fields.Integer(
        string='Failed Count',
        compute='_compute_counts',
    )

    # Totals
    total_tax_due = fields.Float(
        string='Total Tax Due',
        compute='_compute_totals',
        store=True,
    )
    total_penalties = fields.Float(
        string='Total Penalties',
        compute='_compute_totals',
        store=True,
    )
    total_amount_due = fields.Float(
        string='Total Amount Due',
        compute='_compute_totals',
        store=True,
    )

    # E-Filing
    submission_log = fields.Text(
        string='Submission Log',
        readonly=True,
    )
    error_log = fields.Text(
        string='Error Log',
        readonly=True,
    )

    # User
    preparer_id = fields.Many2one(
        'res.users',
        string='Prepared By',
        default=lambda self: self.env.user,
    )
    approver_id = fields.Many2one(
        'res.users',
        string='Approved By',
    )
    approval_date = fields.Datetime(
        string='Approval Date',
    )

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('bir.filing') or '/'
        return super().create(vals)

    @api.depends('form_ids', 'form_ids.state')
    def _compute_counts(self):
        for record in self:
            record.form_count = len(record.form_ids)
            record.submitted_count = len(record.form_ids.filtered(
                lambda f: f.state in ['submitted', 'accepted']
            ))
            record.failed_count = len(record.form_ids.filtered(
                lambda f: f.state == 'rejected'
            ))

    @api.depends('form_ids.tax_due', 'form_ids.penalties', 'form_ids.total_amount_due')
    def _compute_totals(self):
        for record in self:
            record.total_tax_due = sum(record.form_ids.mapped('tax_due'))
            record.total_penalties = sum(record.form_ids.mapped('penalties'))
            record.total_amount_due = sum(record.form_ids.mapped('total_amount_due'))

    def action_generate_forms(self):
        """Generate forms for the filing period."""
        for record in self:
            # Get all form types that need filing for this period
            form_types = self.env['bir.form.type'].search([
                ('active', '=', True),
            ])

            forms_created = []
            for form_type in form_types:
                # Check if this form type is due for this period
                if self._is_form_due(form_type, record.period_start, record.period_end):
                    existing = self.env['bir.form'].search([
                        ('form_type_id', '=', form_type.id),
                        ('period_start', '=', record.period_start),
                        ('period_end', '=', record.period_end),
                        ('company_id', '=', record.company_id.id),
                        ('state', '!=', 'amended'),
                    ], limit=1)

                    if not existing:
                        form = self.env['bir.form'].create({
                            'form_type_id': form_type.id,
                            'period_start': record.period_start,
                            'period_end': record.period_end,
                            'company_id': record.company_id.id,
                            'filing_id': record.id,
                        })
                        forms_created.append(form)

            if forms_created:
                _logger.info(f"Created {len(forms_created)} forms for filing {record.name}")

        return True

    def _is_form_due(self, form_type, period_start, period_end):
        """Check if a form type is due for the given period."""
        if form_type.frequency == 'monthly':
            # Monthly forms are always due
            return True
        elif form_type.frequency == 'quarterly':
            # Quarterly forms due at end of quarter (March, June, Sept, Dec)
            return period_end.month in [3, 6, 9, 12]
        elif form_type.frequency == 'annual':
            # Annual forms due at year end (December)
            return period_end.month == 12
        return False

    def action_compute_all(self):
        """Compute all forms in the batch."""
        for record in self:
            for form in record.form_ids.filtered(lambda f: f.state == 'draft'):
                form.action_compute()
        return True

    def action_validate_all(self):
        """Validate all computed forms."""
        for record in self:
            for form in record.form_ids.filtered(lambda f: f.state == 'computed'):
                try:
                    form.action_validate()
                except ValidationError as e:
                    _logger.error(f"Validation error for form {form.name}: {e}")
        return True

    def action_submit_all(self):
        """Submit all validated forms."""
        for record in self:
            if record.state not in ['draft', 'processing']:
                continue

            record.state = 'processing'
            errors = []

            for form in record.form_ids.filtered(lambda f: f.state == 'validated'):
                try:
                    form.action_submit()
                except Exception as e:
                    errors.append(f"Form {form.name}: {str(e)}")
                    _logger.error(f"Submit error for form {form.name}: {e}")

            if errors:
                record.error_log = '\n'.join(errors)
                record.state = 'failed' if len(errors) == len(record.form_ids) else 'completed'
            else:
                record.state = 'completed'

            record.submission_log = (
                f"Batch submission completed on {fields.Datetime.now()}\n"
                f"Forms: {record.form_count}\n"
                f"Submitted: {record.submitted_count}\n"
                f"Failed: {record.failed_count}\n"
                f"Total Amount: ₱{record.total_amount_due:,.2f}"
            )

        return True

    def action_approve(self):
        """Approve the filing batch."""
        for record in self:
            record.approver_id = self.env.user
            record.approval_date = fields.Datetime.now()
        return True

    def action_reset_draft(self):
        """Reset to draft state."""
        for record in self:
            if record.state == 'completed':
                raise ValidationError(_('Cannot reset completed filings.'))
            record.state = 'draft'
            for form in record.form_ids:
                if form.state not in ['accepted']:
                    form.action_reset_draft()
        return True
