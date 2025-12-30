# -*- coding: utf-8 -*-
{
    'name': 'IPAI BIR Compliance',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'Philippine BIR Tax Compliance - All 36 Forms',
    'description': """
IPAI BIR Compliance Module
==========================

Complete Philippine Bureau of Internal Revenue (BIR) tax compliance:

**Supported BIR Forms:**
- Form 1700 - Annual Income Tax Return (Individual)
- Form 1701 - Annual Income Tax Return (Self-Employed)
- Form 1701A - Annual Income Tax Return (8% Option)
- Form 1601-C - Monthly Withholding Tax (Compensation)
- Form 1601-EQ - Quarterly Expanded Withholding Tax
- Form 1601-FQ - Quarterly Final Withholding Tax
- Form 2550-M - Monthly VAT Declaration
- Form 2550-Q - Quarterly VAT Return
- Form 2551-Q - Quarterly Percentage Tax
- And 27 more forms...

**Payroll Deductions:**
- SSS Contributions (2024 Table)
- PhilHealth (5% total, 2.5% employee share)
- PAGIBIG (2% total, employee share)
- Withholding Tax (Graduated Rates)

**Features:**
- Automated tax calculations
- BIR form generation
- E-filing integration
- Audit trail
- Compliance validation
    """,
    'author': 'InsightPulseAI',
    'website': 'https://insightpulseai.net',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'account',
        'hr',
        'hr_payroll',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        'security/bir_security.xml',
        # Data
        'data/bir_form_types.xml',
        'data/sss_contribution_table.xml',
        'data/tax_brackets.xml',
        # Views
        'views/bir_tax_calculation_views.xml',
        'views/bir_form_views.xml',
        'views/bir_filing_views.xml',
        'views/menu_views.xml',
        # Wizards
        'wizards/bir_filing_wizard_views.xml',
        # Reports
        'reports/bir_form_report.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'external_dependencies': {
        'python': ['cryptography'],
    },
}
