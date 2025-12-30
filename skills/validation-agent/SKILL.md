---
name: validation-agent
description: Run tests, check SLAs, validate compliance. Generates and executes unit/integration/smoke tests. Enforces ≥90% coverage, <2s latency, <0.1% error rate. Use when validating code quality before deployment.
license: Apache-2.0
metadata:
  author: insightpulseai
  version: "1.0"
  domain: testing
  frameworks: ["pytest", "jest", "playwright"]
---

# Validation Agent Skill

Test code, validate SLAs, and enforce quality gates.

## Purpose

This agent ensures all code meets quality standards before deployment. It generates tests, runs them, measures coverage, and validates SLA compliance.

## How to Use

1. **Input code artifact** (Python, SQL, JavaScript)
2. **Input test data** and SLA definitions
3. **Agent generates and runs tests**
4. **Returns coverage report**, latency benchmarks, compliance status

## Test Pyramid

```
        ┌───────────────┐
        │   E2E Tests   │  5% - Critical user journeys
        │   (Smoke)     │
        ├───────────────┤
        │  Integration  │  25% - API + DB + Services
        │    Tests      │
        ├───────────────┤
        │  Unit Tests   │  70% - Fast, isolated, mocked
        │               │
        └───────────────┘
```

## Quality Gates

All PRs must pass these gates:

| Gate | Threshold | Blocking |
|------|-----------|----------|
| Unit test coverage | ≥90% | YES |
| Integration test coverage | ≥80% | YES |
| Latency p99 | <2s | YES |
| Error rate | <0.1% | YES |
| BIR compliance | 100% pass | YES |
| Security scan | No HIGH/CRITICAL | YES |
| Lint/format | Zero errors | YES |

## Test Types

### Unit Tests (70% of tests)
- Fast (<50ms per test)
- Mock external dependencies
- Test business logic in isolation
- Framework: pytest (Python), Jest (JS)

### Integration Tests (25% of tests)
- Test Odoo ↔ Supabase sync
- Test RLS policies work correctly
- Test Edge Functions
- Real database operations
- 100-500ms per test

### Smoke Tests (5% of tests)
- Critical path validation
- Health checks
- Production readiness
- <5s per test

## Example: Generate Tests for BIR Tax Calculation

### Input
```json
{
  "code_artifact": "odoo/addons/ipai_bir_compliance/models/bir_tax_calculation.py",
  "target_coverage": 90,
  "sla": {
    "latency_p99": "2s",
    "error_rate": "0.1%"
  }
}
```

### Output
```python
# tests/test_bir_tax_calculation.py
"""
Tests for BIR Tax Calculation module.
Target coverage: ≥90%
"""

import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import date

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestBIRTaxCalculation(TransactionCase):
    """Test BIR Tax Calculation model with 2024 rates."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee',
            'birthday': date(1990, 1, 1),
        })

    def _create_calculation(self, gross_salary):
        """Helper to create tax calculation record."""
        return self.env['bir.tax.calculation'].create({
            'employee_id': self.employee.id,
            'gross_salary': gross_salary,
        })

    # ==================== SSS TESTS ====================

    def test_sss_minimum_bracket_4000(self):
        """SSS for ₱4,000 salary = ₱180."""
        calc = self._create_calculation(4000)
        self.assertEqual(calc.sss_contribution, 180.00)

    def test_sss_bracket_10000(self):
        """SSS for ₱10,000 salary = ₱450."""
        calc = self._create_calculation(10000)
        self.assertEqual(calc.sss_contribution, 450.00)

    def test_sss_bracket_20000(self):
        """SSS for ₱20,000 salary = ₱900."""
        calc = self._create_calculation(20000)
        self.assertEqual(calc.sss_contribution, 900.00)

    def test_sss_maximum_bracket_30000_plus(self):
        """SSS for ₱30,000+ salary = ₱1,350 (max)."""
        calc = self._create_calculation(50000)
        self.assertEqual(calc.sss_contribution, 1350.00)

    def test_sss_maximum_bracket_100000(self):
        """SSS for ₱100,000 salary = ₱1,350 (max)."""
        calc = self._create_calculation(100000)
        self.assertEqual(calc.sss_contribution, 1350.00)

    # ==================== PHILHEALTH TESTS ====================

    def test_philhealth_under_cap(self):
        """PhilHealth 2.5% under ₱1,250 cap."""
        calc = self._create_calculation(30000)
        expected = 30000 * 0.025  # ₱750
        self.assertEqual(calc.philhealth, 750.00)

    def test_philhealth_at_cap(self):
        """PhilHealth capped at ₱1,250."""
        calc = self._create_calculation(50000)
        # 50000 * 0.025 = 1250, exactly at cap
        self.assertEqual(calc.philhealth, 1250.00)

    def test_philhealth_above_cap(self):
        """PhilHealth capped at ₱1,250 for high earners."""
        calc = self._create_calculation(100000)
        # Would be 2500, but capped
        self.assertEqual(calc.philhealth, 1250.00)

    # ==================== PAGIBIG TESTS ====================

    def test_pagibig_under_cap(self):
        """PAGIBIG 2% under ₱100 cap."""
        calc = self._create_calculation(4000)
        expected = 4000 * 0.02  # ₱80
        self.assertEqual(calc.pagibig, 80.00)

    def test_pagibig_at_cap(self):
        """PAGIBIG capped at ₱100."""
        calc = self._create_calculation(5000)
        # 5000 * 0.02 = 100, exactly at cap
        self.assertEqual(calc.pagibig, 100.00)

    def test_pagibig_above_cap(self):
        """PAGIBIG capped at ₱100 for high earners."""
        calc = self._create_calculation(50000)
        # Would be 1000, but capped
        self.assertEqual(calc.pagibig, 100.00)

    # ==================== WITHHOLDING TAX TESTS ====================

    def test_withholding_tax_exempt_below_250k(self):
        """No withholding tax for annual income ≤₱250,000."""
        calc = self._create_calculation(20000)  # ₱240k annual
        self.assertEqual(calc.withholding_tax, 0.00)

    def test_withholding_tax_first_bracket(self):
        """15% bracket for ₱250,001-₱400,000 annual."""
        calc = self._create_calculation(30000)  # ₱360k annual
        # Taxable: 360k - (SSS+PhilHealth+PAGIBIG)*12
        # Tax = (360k - 250k) * 0.15 / 12
        self.assertGreater(calc.withholding_tax, 0)

    def test_withholding_tax_high_earner(self):
        """Higher brackets for high earners."""
        calc = self._create_calculation(200000)  # ₱2.4M annual
        self.assertGreater(calc.withholding_tax, 10000)

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
        """Net = Gross - SSS - PhilHealth - PAGIBIG - Tax."""
        calc = self._create_calculation(50000)
        expected_deductions = (
            calc.sss_contribution +
            calc.philhealth +
            calc.pagibig +
            calc.withholding_tax
        )
        expected_net = calc.gross_salary - expected_deductions
        self.assertAlmostEqual(calc.net_salary, expected_net, places=2)

    # ==================== VALIDATION TESTS ====================

    def test_negative_salary_rejected(self):
        """Negative salary raises ValidationError."""
        with self.assertRaises(ValidationError):
            self._create_calculation(-1000)

    def test_zero_salary_accepted(self):
        """Zero salary is valid (unpaid leave)."""
        calc = self._create_calculation(0)
        self.assertEqual(calc.net_salary, 0)

    # ==================== EDGE CASES ====================

    def test_decimal_salary(self):
        """Decimal salary is handled correctly."""
        calc = self._create_calculation(45678.90)
        self.assertIsInstance(calc.sss_contribution, float)
        self.assertIsInstance(calc.net_salary, float)

    def test_minimum_wage(self):
        """Minimum wage (₱610/day * 26 = ₱15,860)."""
        calc = self._create_calculation(15860)
        self.assertGreater(calc.net_salary, 0)


class TestBIRTaxPerformance(TransactionCase):
    """Performance tests for BIR Tax Calculation."""

    def test_bulk_calculation_under_2s(self):
        """1000 calculations complete in <2s."""
        import time

        employee = self.env['hr.employee'].create({'name': 'Perf Test'})

        start = time.time()
        for i in range(1000):
            self.env['bir.tax.calculation'].create({
                'employee_id': employee.id,
                'gross_salary': 30000 + i,
            })
        elapsed = time.time() - start

        self.assertLess(elapsed, 2.0, f"Bulk creation took {elapsed:.2f}s")


class TestBIRCompliance(TransactionCase):
    """Compliance tests against BIR 2024 rules."""

    def test_all_deductions_match_bir_table(self):
        """Verify deductions match official BIR 2024 tables."""
        test_cases = [
            # (gross, expected_sss, expected_philhealth, expected_pagibig)
            (10000, 450.00, 250.00, 100.00),
            (20000, 900.00, 500.00, 100.00),
            (30000, 1350.00, 750.00, 100.00),
            (50000, 1350.00, 1250.00, 100.00),
        ]

        employee = self.env['hr.employee'].create({'name': 'BIR Test'})

        for gross, exp_sss, exp_ph, exp_pag in test_cases:
            calc = self.env['bir.tax.calculation'].create({
                'employee_id': employee.id,
                'gross_salary': gross,
            })
            self.assertEqual(
                calc.sss_contribution, exp_sss,
                f"SSS mismatch for ₱{gross}: got {calc.sss_contribution}"
            )
            self.assertEqual(
                calc.philhealth, exp_ph,
                f"PhilHealth mismatch for ₱{gross}: got {calc.philhealth}"
            )
            self.assertEqual(
                calc.pagibig, exp_pag,
                f"PAGIBIG mismatch for ₱{gross}: got {calc.pagibig}"
            )
```

## Coverage Report Format

```
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
models/bir_tax_calculation.py              85      4    95%
models/bir_forms.py                       120      8    93%
controllers/webhook.py                     45      3    93%
-----------------------------------------------------------
TOTAL                                     250     15    94%

✅ Coverage: 94% (threshold: 90%)
✅ All 28 tests passed
✅ Latency p99: 1.2s (threshold: 2s)
✅ Error rate: 0.00% (threshold: 0.1%)
✅ BIR Compliance: 100% (all tables verified)
```

## SLA Validation

### Latency Benchmarks
```python
def test_api_latency_p99():
    """Verify API latency is under 2s at p99."""
    import statistics
    import requests

    latencies = []
    for _ in range(100):
        start = time.time()
        response = requests.get('/api/v1/bir/calculate')
        latencies.append(time.time() - start)

    p99 = sorted(latencies)[98]  # 99th percentile
    assert p99 < 2.0, f"p99 latency {p99:.2f}s exceeds 2s threshold"
```

### Error Rate Check
```python
def test_error_rate_under_threshold():
    """Verify error rate is under 0.1%."""
    total_requests = 1000
    errors = 0

    for _ in range(total_requests):
        response = requests.post('/api/v1/bir/validate', json=valid_data)
        if response.status_code >= 400:
            errors += 1

    error_rate = errors / total_requests
    assert error_rate < 0.001, f"Error rate {error_rate:.2%} exceeds 0.1%"
```

## Skill Boundaries

### What This Skill CAN Do
- Generate unit tests with high coverage
- Generate integration tests
- Generate performance benchmarks
- Validate SLA compliance
- Create coverage reports
- Check BIR compliance

### What This Skill CANNOT Do
- Extract specs from docs (use `documentation-parser`)
- Validate tax rules (use `compliance-validator`)
- Generate application code (use `code-generator`)
- Write SQL queries (use `sql-agent`)
- Deploy systems (use `deployment-orchestrator`)

## Rules

- Generate tests BEFORE running code
- Mock external dependencies in unit tests
- Measure latency with realistic data
- Flag coverage gaps
- **DO NOT** override SLA thresholds
- **DO NOT** approve code with <90% coverage
- **DO NOT** deploy if smoke tests fail
