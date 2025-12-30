# -*- coding: utf-8 -*-
"""Tests for BIR Tax Calculation module."""

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestBIRTaxCalculation(TransactionCase):
    """Test BIR Tax Calculation with 2024 rates."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Employee = cls.env['hr.employee']
        cls.TaxCalc = cls.env['bir.tax.calculation']
        cls.SSSTable = cls.env['bir.sss.contribution']

        # Create test employee
        cls.employee = cls.Employee.create({
            'name': 'Test Employee',
        })

    def _create_calculation(self, gross_salary, **kwargs):
        """Helper to create tax calculation."""
        vals = {
            'employee_id': self.employee.id,
            'gross_salary': gross_salary,
        }
        vals.update(kwargs)
        return self.TaxCalc.create(vals)

    # ==================== SSS TESTS ====================

    def test_sss_minimum_bracket(self):
        """SSS for minimum salary (< ₱4,250)."""
        calc = self._create_calculation(4000)
        self.assertEqual(calc.sss_contribution, 180.00)

    def test_sss_mid_bracket(self):
        """SSS for mid-range salary (₱10,000)."""
        calc = self._create_calculation(10000)
        self.assertEqual(calc.sss_contribution, 450.00)

    def test_sss_maximum_bracket(self):
        """SSS for high salary (₱30,000+) = max ₱1,350."""
        calc = self._create_calculation(50000)
        self.assertEqual(calc.sss_contribution, 1350.00)

    def test_sss_very_high_salary(self):
        """SSS for very high salary still capped at ₱1,350."""
        calc = self._create_calculation(200000)
        self.assertEqual(calc.sss_contribution, 1350.00)

    # ==================== PHILHEALTH TESTS ====================

    def test_philhealth_under_cap(self):
        """PhilHealth 2.5% for low salary."""
        calc = self._create_calculation(30000)
        # 30000 * 0.025 = 750
        self.assertEqual(calc.philhealth, 750.00)

    def test_philhealth_at_cap(self):
        """PhilHealth capped at ₱1,250."""
        calc = self._create_calculation(50000)
        # 50000 * 0.025 = 1250
        self.assertEqual(calc.philhealth, 1250.00)

    def test_philhealth_above_cap(self):
        """PhilHealth capped at ₱1,250 for high earners."""
        calc = self._create_calculation(100000)
        # Would be 2500, but capped
        self.assertEqual(calc.philhealth, 1250.00)

    # ==================== PAGIBIG TESTS ====================

    def test_pagibig_low_salary(self):
        """PAGIBIG for low salary (< ₱1,500) = 1%."""
        calc = self._create_calculation(1000)
        # 1000 * 0.01 = 10
        self.assertEqual(calc.pagibig, 10.00)

    def test_pagibig_standard(self):
        """PAGIBIG 2% for standard salary."""
        calc = self._create_calculation(4000)
        # 4000 * 0.02 = 80
        self.assertEqual(calc.pagibig, 80.00)

    def test_pagibig_capped(self):
        """PAGIBIG capped at ₱100."""
        calc = self._create_calculation(10000)
        # 10000 * 0.02 = 200, but capped
        self.assertEqual(calc.pagibig, 100.00)

    # ==================== WITHHOLDING TAX TESTS ====================

    def test_withholding_exempt(self):
        """No withholding for annual ≤₱250,000."""
        calc = self._create_calculation(20000)
        # 20000 * 12 = 240000 annual, below threshold
        self.assertEqual(calc.withholding_tax, 0.00)
        self.assertIn('0%', calc.tax_bracket)

    def test_withholding_first_bracket(self):
        """15% bracket for ₱250,001-₱400,000 annual."""
        calc = self._create_calculation(30000)
        # 30000 * 12 = 360000 annual
        # Taxable = 360000 - (deductions * 12)
        self.assertGreater(calc.withholding_tax, 0)
        self.assertIn('15%', calc.tax_bracket)

    def test_withholding_second_bracket(self):
        """20% bracket for ₱400,001-₱800,000 annual."""
        calc = self._create_calculation(50000)
        # 50000 * 12 = 600000 annual
        self.assertGreater(calc.withholding_tax, 0)
        self.assertIn('20%', calc.tax_bracket)

    def test_withholding_minimum_wage_exempt(self):
        """Minimum wage earners are exempt."""
        calc = self._create_calculation(15860, is_minimum_wage_earner=True)
        self.assertEqual(calc.withholding_tax, 0.00)
        self.assertEqual(calc.tax_bracket, 'EXEMPT (MWE)')

    # ==================== NET SALARY TESTS ====================

    def test_net_salary_positive(self):
        """Net salary must be positive."""
        calc = self._create_calculation(50000)
        self.assertGreater(calc.net_salary, 0)

    def test_net_salary_less_than_gross(self):
        """Net salary must be less than gross."""
        calc = self._create_calculation(50000)
        self.assertLess(calc.net_salary, calc.gross_salary)

    def test_net_salary_calculation(self):
        """Verify net = gross - all deductions."""
        calc = self._create_calculation(50000)
        expected_net = (
            calc.gross_salary -
            calc.sss_contribution -
            calc.philhealth -
            calc.pagibig -
            calc.withholding_tax
        )
        self.assertAlmostEqual(calc.net_salary, expected_net, places=2)

    # ==================== VALIDATION TESTS ====================

    def test_negative_salary_rejected(self):
        """Negative salary raises ValidationError."""
        with self.assertRaises(ValidationError):
            self._create_calculation(-1000)

    def test_zero_salary_accepted(self):
        """Zero salary is valid (e.g., unpaid leave)."""
        calc = self._create_calculation(0)
        self.assertEqual(calc.net_salary, 0)

    # ==================== STATE TESTS ====================

    def test_initial_state_draft(self):
        """New calculation starts in draft state."""
        calc = self._create_calculation(50000)
        self.assertEqual(calc.state, 'draft')

    def test_action_calculate(self):
        """Calculate action moves to calculated state."""
        calc = self._create_calculation(50000)
        calc.action_calculate()
        self.assertEqual(calc.state, 'calculated')
        self.assertTrue(calc.calculation_log)

    def test_action_validate(self):
        """Validate action moves to validated state."""
        calc = self._create_calculation(50000)
        calc.action_calculate()
        calc.action_validate()
        self.assertEqual(calc.state, 'validated')

    def test_validate_before_calculate_fails(self):
        """Cannot validate without calculating first."""
        calc = self._create_calculation(50000)
        with self.assertRaises(ValidationError):
            calc.action_validate()

    # ==================== EXEMPTION TESTS ====================

    def test_senior_citizen_exemption(self):
        """Senior citizen gets additional exemption."""
        calc = self._create_calculation(50000, is_senior_citizen=True)
        calc_normal = self._create_calculation(50000, is_senior_citizen=False)

        # Senior should have lower taxable income
        self.assertLess(
            calc.taxable_income_after_deductions,
            calc_normal.taxable_income_after_deductions
        )

    def test_pwd_exemption(self):
        """PWD gets additional exemption."""
        calc = self._create_calculation(50000, is_pwd=True)
        calc_normal = self._create_calculation(50000, is_pwd=False)

        # PWD should have lower taxable income
        self.assertLess(
            calc.taxable_income_after_deductions,
            calc_normal.taxable_income_after_deductions
        )


class TestBIRFormGeneration(TransactionCase):
    """Test BIR Form generation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Form = cls.env['bir.form']
        cls.FormType = cls.env['bir.form.type']

    def test_form_types_loaded(self):
        """Verify BIR form types are loaded."""
        form_1601c = self.FormType.search([('code', '=', '1601-C')], limit=1)
        self.assertTrue(form_1601c)
        self.assertEqual(form_1601c.category, 'withholding_tax')
        self.assertEqual(form_1601c.frequency, 'monthly')

    def test_form_1700_loaded(self):
        """Verify Form 1700 is loaded."""
        form_1700 = self.FormType.search([('code', '=', '1700')], limit=1)
        self.assertTrue(form_1700)
        self.assertEqual(form_1700.category, 'income_tax')
        self.assertEqual(form_1700.frequency, 'annual')

    def test_form_2550q_loaded(self):
        """Verify Form 2550-Q is loaded."""
        form_2550q = self.FormType.search([('code', '=', '2550-Q')], limit=1)
        self.assertTrue(form_2550q)
        self.assertEqual(form_2550q.category, 'vat')
        self.assertEqual(form_2550q.frequency, 'quarterly')


class TestSSSContributionTable(TransactionCase):
    """Test SSS Contribution Table."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.SSSTable = cls.env['bir.sss.contribution']

    def test_sss_table_loaded(self):
        """Verify SSS table is loaded."""
        brackets = self.SSSTable.search([('year', '=', 2024)])
        self.assertGreater(len(brackets), 0)

    def test_sss_get_contribution(self):
        """Test get_contribution helper method."""
        contrib = self.SSSTable.get_contribution(50000)
        self.assertEqual(contrib['employee_share'], 1350.00)
        self.assertGreater(contrib['employer_share'], 0)

    def test_sss_total_matches(self):
        """Verify total = employee + employer."""
        brackets = self.SSSTable.search([('year', '=', 2024)])
        for bracket in brackets:
            self.assertEqual(
                bracket.total_contribution,
                bracket.employee_share + bracket.employer_share
            )
