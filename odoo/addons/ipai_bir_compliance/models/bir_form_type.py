# -*- coding: utf-8 -*-
"""BIR Form Type definitions for all 36 eBIR forms."""

from odoo import models, fields


class BIRFormType(models.Model):
    """BIR Form Type - Reference data for all 36 eBIR forms."""

    _name = 'bir.form.type'
    _description = 'BIR Form Type'
    _order = 'sequence, code'

    name = fields.Char(
        string='Form Name',
        required=True,
    )
    code = fields.Char(
        string='Form Code',
        required=True,
        index=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    category = fields.Selection([
        ('income_tax', 'Income Tax'),
        ('withholding_tax', 'Withholding Tax'),
        ('vat', 'VAT & Percentage Tax'),
        ('excise', 'Excise Tax'),
        ('capital_gains', 'Capital Gains & Other'),
        ('transfer', 'Transfer Taxes'),
        ('documentary', 'Documentary Stamp Tax'),
        ('registration', 'Registration'),
    ], string='Category', required=True)
    frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
        ('one_time', 'One-Time'),
        ('as_needed', 'As Needed'),
    ], string='Filing Frequency', required=True)
    description = fields.Text(string='Description')
    instructions = fields.Text(string='Filing Instructions')
    deadline_day = fields.Integer(
        string='Deadline Day',
        help='Day of month for deadline (e.g., 10 = 10th)',
    )
    deadline_offset = fields.Selection([
        ('following_month', 'Following Month'),
        ('following_quarter', 'Following Quarter'),
        ('following_year', 'Following Year'),
        ('within_30_days', 'Within 30 Days'),
    ], string='Deadline Offset')
    active = fields.Boolean(string='Active', default=True)

    # E-Filing fields
    ebirforms_enabled = fields.Boolean(
        string='eBIRForms Enabled',
        default=True,
    )
    efps_enabled = fields.Boolean(
        string='eFPS Enabled',
        default=False,
        help='Electronic Filing and Payment System',
    )
    attachment_required = fields.Boolean(
        string='Attachments Required',
        default=False,
    )
    attachment_types = fields.Char(
        string='Required Attachment Types',
        help='Comma-separated list of required attachments',
    )

    _sql_constraints = [
        ('code_uniq', 'UNIQUE(code)', 'Form code must be unique!'),
    ]
