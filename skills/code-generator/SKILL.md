---
name: code-generator
description: Generate production-ready code (Odoo 18 Python, FastAPI, React, SQL) from specifications. Incorporates compliance rules, error handling, logging, and RLS policies. Generates both code and unit tests. Use when implementing Docs2Code pipeline or building features from specifications.
license: Apache-2.0
metadata:
  author: insightpulseai
  version: "1.0"
  domain: code-generation
  frameworks: ["odoo-18-ce", "fastapi", "react", "postgresql"]
---

# Code Generator Skill

Generate production-ready code from specifications.

## Purpose

This agent transforms structured specifications (from `documentation-parser`) and compliance rules (from `compliance-validator`) into deployable code with tests.

## How to Use

1. **Input specification document** (from DocumentationParser)
2. **Input compliance rules** (from ComplianceValidator)
3. **Select target framework** (Odoo, FastAPI, React, SQL)
4. **Agent generates code** with tests

## Supported Frameworks

### Odoo 18 CE
- Model definitions with fields, constraints, methods
- Webhook emitters for Supabase sync
- Validation methods and state machines
- XML views (form, tree, kanban)
- Format: Python class definitions

### FastAPI
- REST endpoints with request/response schemas
- Pydantic models for validation
- Database connection pooling (asyncpg)
- Error handling and structured logging
- Format: Python async functions

### React (TypeScript)
- Components using hooks (useState, useEffect, useContext)
- Supabase real-time subscriptions
- Form validation with react-hook-form
- Format: TypeScript components

### PostgreSQL
- CREATE TABLE with RLS policies
- Window functions, aggregations, CTEs
- Triggers and stored procedures
- Supabase Edge Functions (TypeScript)
- Format: SQL with comments

## Code Generation Pattern

```
1. Read specification → extract requirements
2. Read compliance rules → extract constraints
3. Generate skeleton → with error handling
4. Add logging → at entry/exit of functions
5. Generate unit tests → minimum 90% coverage
6. Add docstrings → and type hints
7. Output deployment notes → and dependencies
```

## Example: Generate Odoo BIR Tax Model

### Input
```json
{
  "spec": {
    "model": "bir.tax.calculation",
    "fields": [
      {"name": "employee_id", "type": "many2one", "relation": "hr.employee"},
      {"name": "gross_salary", "type": "float"},
      {"name": "sss_contribution", "type": "float", "computed": true},
      {"name": "philhealth", "type": "float", "computed": true},
      {"name": "pagibig", "type": "float", "computed": true},
      {"name": "withholding_tax", "type": "float", "computed": true},
      {"name": "net_salary", "type": "float", "computed": true}
    ],
    "constraints": ["gross_salary >= 0", "all_deductions_valid"]
  },
  "compliance_rules": {
    "sss_2024": "SSS Contribution Table 2024",
    "philhealth_2024": "2.5% employee share, max ₱1,250",
    "pagibig_2024": "2% employee share, max ₱100"
  },
  "target_framework": "odoo-18-ce"
}
```

### Output
```python
# -*- coding: utf-8 -*-
"""BIR Tax Calculation Model for Odoo 18 CE.

This module implements Philippine tax calculations including:
- SSS contributions (2024 table)
- PhilHealth (2.5% employee share)
- PAGIBIG (2% employee share)
- Withholding tax (graduated rates)
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class BIRTaxCalculation(models.Model):
    _name = 'bir.tax.calculation'
    _description = 'BIR Tax Calculation'
    _order = 'create_date desc'

    # --- Fields ---
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
    )
    gross_salary = fields.Float(
        string='Gross Salary',
        required=True,
        help='Monthly gross salary in PHP',
    )
    sss_contribution = fields.Float(
        string='SSS Contribution',
        compute='_compute_sss',
        store=True,
    )
    philhealth = fields.Float(
        string='PhilHealth',
        compute='_compute_philhealth',
        store=True,
    )
    pagibig = fields.Float(
        string='PAGIBIG',
        compute='_compute_pagibig',
        store=True,
    )
    withholding_tax = fields.Float(
        string='Withholding Tax',
        compute='_compute_withholding_tax',
        store=True,
    )
    net_salary = fields.Float(
        string='Net Salary',
        compute='_compute_net_salary',
        store=True,
    )

    # --- SSS 2024 Table ---
    SSS_TABLE = [
        (4250, 180.00),
        (4750, 202.50),
        (5250, 225.00),
        (5750, 247.50),
        (6250, 270.00),
        (6750, 292.50),
        (7250, 315.00),
        (7750, 337.50),
        (8250, 360.00),
        (8750, 382.50),
        (9250, 405.00),
        (9750, 427.50),
        (10250, 450.00),
        (10750, 472.50),
        (11250, 495.00),
        (11750, 517.50),
        (12250, 540.00),
        (12750, 562.50),
        (13250, 585.00),
        (13750, 607.50),
        (14250, 630.00),
        (14750, 652.50),
        (15250, 675.00),
        (15750, 697.50),
        (16250, 720.00),
        (16750, 742.50),
        (17250, 765.00),
        (17750, 787.50),
        (18250, 810.00),
        (18750, 832.50),
        (19250, 855.00),
        (19750, 877.50),
        (20250, 900.00),
        (24750, 1125.00),
        (29750, 1350.00),
        (float('inf'), 1350.00),  # Max contribution
    ]

    @api.depends('gross_salary')
    def _compute_sss(self):
        """Compute SSS contribution based on 2024 table."""
        for record in self:
            _logger.info(f"Computing SSS for gross_salary={record.gross_salary}")
            contribution = 0.0
            for threshold, amount in self.SSS_TABLE:
                if record.gross_salary <= threshold:
                    contribution = amount
                    break
            record.sss_contribution = contribution

    @api.depends('gross_salary')
    def _compute_philhealth(self):
        """Compute PhilHealth: 2.5% employee share, max ₱1,250."""
        for record in self:
            contribution = record.gross_salary * 0.025
            record.philhealth = min(contribution, 1250.00)

    @api.depends('gross_salary')
    def _compute_pagibig(self):
        """Compute PAGIBIG: 2% employee share, max ₱100."""
        for record in self:
            contribution = record.gross_salary * 0.02
            record.pagibig = min(contribution, 100.00)

    @api.depends('gross_salary', 'sss_contribution', 'philhealth', 'pagibig')
    def _compute_withholding_tax(self):
        """Compute withholding tax based on 2024 graduated rates."""
        for record in self:
            # Monthly taxable income (annualized for calculation)
            annual_gross = record.gross_salary * 12
            annual_deductions = (
                record.sss_contribution + record.philhealth + record.pagibig
            ) * 12
            taxable_income = annual_gross - annual_deductions

            # 2024 Tax Brackets
            if taxable_income <= 250000:
                annual_tax = 0
            elif taxable_income <= 400000:
                annual_tax = (taxable_income - 250000) * 0.15
            elif taxable_income <= 800000:
                annual_tax = 22500 + (taxable_income - 400000) * 0.20
            elif taxable_income <= 2000000:
                annual_tax = 102500 + (taxable_income - 800000) * 0.25
            elif taxable_income <= 8000000:
                annual_tax = 402500 + (taxable_income - 2000000) * 0.30
            else:
                annual_tax = 2202500 + (taxable_income - 8000000) * 0.35

            record.withholding_tax = annual_tax / 12

    @api.depends(
        'gross_salary', 'sss_contribution', 'philhealth',
        'pagibig', 'withholding_tax'
    )
    def _compute_net_salary(self):
        """Compute net salary after all deductions."""
        for record in self:
            record.net_salary = (
                record.gross_salary
                - record.sss_contribution
                - record.philhealth
                - record.pagibig
                - record.withholding_tax
            )

    @api.constrains('gross_salary')
    def _check_gross_salary(self):
        """Validate gross salary is non-negative."""
        for record in self:
            if record.gross_salary < 0:
                raise ValidationError(
                    _('Gross salary cannot be negative.')
                )
```

## Generated Test Suite

```python
# tests/test_bir_tax_calculation.py
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestBIRTaxCalculation(TransactionCase):
    """Test BIR Tax Calculation model."""

    def setUp(self):
        super().setUp()
        self.employee = self.env['hr.employee'].create({
            'name': 'Test Employee',
        })

    def test_sss_minimum_bracket(self):
        """Test SSS for minimum salary bracket."""
        calc = self.env['bir.tax.calculation'].create({
            'employee_id': self.employee.id,
            'gross_salary': 4000,
        })
        self.assertEqual(calc.sss_contribution, 180.00)

    def test_sss_maximum_bracket(self):
        """Test SSS for maximum salary (₱30,000+)."""
        calc = self.env['bir.tax.calculation'].create({
            'employee_id': self.employee.id,
            'gross_salary': 50000,
        })
        self.assertEqual(calc.sss_contribution, 1350.00)

    def test_philhealth_under_cap(self):
        """Test PhilHealth under ₱1,250 cap."""
        calc = self.env['bir.tax.calculation'].create({
            'employee_id': self.employee.id,
            'gross_salary': 30000,
        })
        self.assertEqual(calc.philhealth, 750.00)  # 30000 * 0.025

    def test_philhealth_capped(self):
        """Test PhilHealth capped at ₱1,250."""
        calc = self.env['bir.tax.calculation'].create({
            'employee_id': self.employee.id,
            'gross_salary': 100000,
        })
        self.assertEqual(calc.philhealth, 1250.00)

    def test_pagibig_capped(self):
        """Test PAGIBIG capped at ₱100."""
        calc = self.env['bir.tax.calculation'].create({
            'employee_id': self.employee.id,
            'gross_salary': 50000,
        })
        self.assertEqual(calc.pagibig, 100.00)

    def test_withholding_tax_exempt(self):
        """Test no withholding for ≤₱250,000 annual."""
        calc = self.env['bir.tax.calculation'].create({
            'employee_id': self.employee.id,
            'gross_salary': 20000,  # ₱240,000 annual
        })
        self.assertEqual(calc.withholding_tax, 0.00)

    def test_negative_salary_rejected(self):
        """Test that negative salary raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.env['bir.tax.calculation'].create({
                'employee_id': self.employee.id,
                'gross_salary': -1000,
            })

    def test_net_salary_calculation(self):
        """Test complete net salary calculation."""
        calc = self.env['bir.tax.calculation'].create({
            'employee_id': self.employee.id,
            'gross_salary': 50000,
        })
        expected_deductions = 1350 + 1250 + 100  # SSS + PhilHealth + PAGIBIG
        # Plus withholding tax (calculated based on taxable income)
        self.assertGreater(calc.net_salary, 0)
        self.assertLess(calc.net_salary, calc.gross_salary)
```

## Skill Boundaries

### What This Skill CAN Do
- Generate Odoo models with computed fields
- Generate FastAPI endpoints with validation
- Generate React components with hooks
- Generate SQL with RLS policies
- Generate unit tests (≥90% coverage)
- Add logging, error handling, docstrings

### What This Skill CANNOT Do
- Extract specs from docs (use `documentation-parser`)
- Validate compliance rules (use `compliance-validator`)
- Execute SQL queries (use `sql-agent`)
- Deploy code (use `deployment-orchestrator`)

## Rules

- Always include error handling (try/except)
- Add comprehensive logging with structlog
- Generate test cases automatically
- Use type hints (Python) or interfaces (TypeScript)
- Follow framework conventions (PEP 8, Odoo guidelines)
- **DO NOT** hardcode credentials
- **DO NOT** generate untested code
- **DO NOT** skip compliance checks
