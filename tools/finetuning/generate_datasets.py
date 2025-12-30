#!/usr/bin/env python3
"""
Fine-Tuning Dataset Generator for InsightPulseAI Agent Skills.

This script generates training datasets for fine-tuning LLMs on:
- Documentation parsing (Odoo, Supabase, BIR)
- Compliance validation (Philippine tax rules)
- Code generation (Odoo, FastAPI, SQL)
- SQL transformations (bronze/silver/gold)
- Test generation and validation

Usage:
    python generate_datasets.py --agent documentation-parser --output ./datasets/
    python generate_datasets.py --all --output ./datasets/

References:
    - https://huggingface.co/spaces/HuggingFaceTB/smol-training-playbook
    - https://agentskills.io/specification
"""

import argparse
import json
import random
from pathlib import Path
from typing import List, Dict, Any
from datetime import date


class DatasetGenerator:
    """Generate fine-tuning datasets for specialized agents."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_all(self):
        """Generate datasets for all agents."""
        print("Generating datasets for all agents...")

        datasets = {
            'documentation-parser': self.generate_doc_parser_examples(),
            'compliance-validator': self.generate_compliance_examples(),
            'code-generator': self.generate_codegen_examples(),
            'sql-agent': self.generate_sql_examples(),
            'validation-agent': self.generate_validation_examples(),
        }

        for agent_name, examples in datasets.items():
            self._save_dataset(agent_name, examples)
            print(f"  ✓ {agent_name}: {len(examples)} examples")

        print(f"\nDatasets saved to: {self.output_dir}")

    def generate_doc_parser_examples(self) -> List[Dict[str, Any]]:
        """Generate examples for documentation-parser agent."""
        examples = []

        # Example 1: Extract Odoo webhook models
        examples.append({
            "input": """
Documentation: Odoo 18 Webhook Configuration
Event Types: Supported on key models including:
- res.partner (customers/vendors)
- account.invoice (invoices)
- account.payment (payments)
- sale.order (sales orders)
- purchase.order (purchase orders)
- hr.employee (employees)
- account.move (journal entries)

Headers: Custom headers for authentication
- X-API-Key: API key for validation
- Authorization: Bearer <TOKEN>

Signatures: HMAC-SHA256 signature validation with shared secret
Retries: Automatic retries with exponential backoff (up to 5 attempts)

Task: Extract webhook models and authentication methods
""",
            "output": {
                "extracted_specs": {
                    "webhook_models": [
                        "res.partner",
                        "account.invoice",
                        "account.payment",
                        "sale.order",
                        "purchase.order",
                        "hr.employee",
                        "account.move"
                    ],
                    "event_types": ["create", "write", "unlink"],
                    "authentication": {
                        "methods": ["X-API-Key", "Bearer Token"],
                        "signature": "HMAC-SHA256"
                    },
                    "retry_strategy": {
                        "type": "exponential_backoff",
                        "max_attempts": 5
                    }
                },
                "confidence": "high",
                "source": "Odoo 18 Webhook Configuration"
            }
        })

        # Example 2: Extract Supabase RLS policy
        examples.append({
            "input": """
Documentation: Supabase Row Level Security
Table: silver.invoices

Policy: approver_pending_invoices
- Role: approver
- Operation: UPDATE
- Condition: approval_state = 'pending'
- Check: approval_state IN ('approved', 'rejected')

Policy: analyst_read_all
- Role: analyst
- Operation: SELECT
- Condition: true (all records visible)

Task: Extract RLS policies for silver.invoices table
""",
            "output": {
                "extracted_specs": {
                    "table": "silver.invoices",
                    "policies": [
                        {
                            "name": "approver_pending_invoices",
                            "role": "approver",
                            "operation": "UPDATE",
                            "using_condition": "approval_state = 'pending'",
                            "with_check": "approval_state IN ('approved', 'rejected')"
                        },
                        {
                            "name": "analyst_read_all",
                            "role": "analyst",
                            "operation": "SELECT",
                            "using_condition": "true"
                        }
                    ]
                },
                "confidence": "high",
                "source": "Supabase Row Level Security"
            }
        })

        # Example 3: Extract BIR form requirements
        examples.append({
            "input": """
Documentation: BIR Form 1601-C
Monthly Remittance of Taxes Withheld on Compensation

Required Fields:
- TIN: Taxpayer Identification Number
- Registered Name: Company name as registered with BIR
- RDO Code: Revenue District Office code
- Period: Month and year of compensation
- Total Compensation Income: Sum of all employee salaries
- Tax Withheld: Total withholding tax for the period

Filing Deadline: 10th day of the following month
E-Filing: Available via eBIRForms

Task: Extract form requirements for BIR 1601-C
""",
            "output": {
                "extracted_specs": {
                    "form_code": "1601-C",
                    "form_name": "Monthly Remittance of Taxes Withheld on Compensation",
                    "category": "withholding_tax",
                    "frequency": "monthly",
                    "required_fields": [
                        {"name": "TIN", "type": "string", "required": True},
                        {"name": "Registered Name", "type": "string", "required": True},
                        {"name": "RDO Code", "type": "string", "required": True},
                        {"name": "Period", "type": "date_range", "required": True},
                        {"name": "Total Compensation Income", "type": "decimal", "required": True},
                        {"name": "Tax Withheld", "type": "decimal", "required": True}
                    ],
                    "deadline": {
                        "day": 10,
                        "offset": "following_month"
                    },
                    "efiling_available": True
                },
                "confidence": "high",
                "source": "BIR Form 1601-C Documentation"
            }
        })

        # Add more examples...
        examples.extend(self._generate_more_doc_parser_examples())

        return examples

    def generate_compliance_examples(self) -> List[Dict[str, Any]]:
        """Generate examples for compliance-validator agent."""
        examples = []

        # SSS contribution examples
        sss_test_cases = [
            (4000, 180.00, "minimum bracket"),
            (10000, 450.00, "mid bracket"),
            (20000, 900.00, "upper mid bracket"),
            (30000, 1350.00, "maximum bracket"),
            (50000, 1350.00, "above maximum, capped"),
            (100000, 1350.00, "high salary, capped"),
        ]

        for gross, expected_sss, description in sss_test_cases:
            examples.append({
                "input": {
                    "transaction_type": "payslip",
                    "gross_salary": gross,
                    "validate": ["sss_contribution"]
                },
                "output": {
                    "compliant": True,
                    "calculations": {
                        "sss_contribution": expected_sss,
                        "calculation_basis": f"SSS 2024 Table - {description}"
                    },
                    "rules_applied": ["SSS_CONTRIBUTION_TABLE_2024"]
                }
            })

        # PhilHealth examples
        philhealth_cases = [
            (30000, 750.00, False),  # 30000 * 0.025 = 750
            (50000, 1250.00, True),   # 50000 * 0.025 = 1250 (at cap)
            (100000, 1250.00, True),  # Capped at 1250
        ]

        for gross, expected_ph, is_capped in philhealth_cases:
            examples.append({
                "input": {
                    "transaction_type": "payslip",
                    "gross_salary": gross,
                    "validate": ["philhealth"]
                },
                "output": {
                    "compliant": True,
                    "calculations": {
                        "philhealth": expected_ph,
                        "rate": 0.025,
                        "capped": is_capped,
                        "cap_amount": 1250.00
                    },
                    "rules_applied": ["PHILHEALTH_2024"]
                }
            })

        # Validation error examples
        examples.append({
            "input": {
                "transaction_type": "payslip",
                "gross_salary": 50000,
                "sss_contribution": 0,
                "philhealth": 1200,
                "pagibig": 50
            },
            "output": {
                "compliant": False,
                "violations": [
                    {
                        "rule": "SSS_CONTRIBUTION_REQUIRED",
                        "field": "sss_contribution",
                        "expected": 1350.00,
                        "actual": 0,
                        "severity": "critical",
                        "reference": "SSS Contribution Table 2024"
                    },
                    {
                        "rule": "PHILHEALTH_UNDERPAID",
                        "field": "philhealth",
                        "expected": 1250.00,
                        "actual": 1200,
                        "severity": "warning",
                        "reference": "PhilHealth Rate 2024"
                    },
                    {
                        "rule": "PAGIBIG_UNDERPAID",
                        "field": "pagibig",
                        "expected": 100.00,
                        "actual": 50,
                        "severity": "warning",
                        "reference": "PAGIBIG Contribution Table 2024"
                    }
                ],
                "corrected_values": {
                    "sss_contribution": 1350.00,
                    "philhealth": 1250.00,
                    "pagibig": 100.00,
                    "total_deductions": 2700.00
                }
            }
        })

        # Tax bracket examples
        tax_bracket_cases = [
            (20000, 240000, "0%", 0),  # Annual 240k, exempt
            (30000, 360000, "15%", (360000 - 250000) * 0.15 / 12),
            (50000, 600000, "20%", (22500 + (600000 - 400000) * 0.20) / 12),
        ]

        for monthly, annual, bracket, expected_tax in tax_bracket_cases:
            examples.append({
                "input": {
                    "transaction_type": "withholding_tax",
                    "gross_salary": monthly,
                    "annual_income": annual
                },
                "output": {
                    "compliant": True,
                    "calculations": {
                        "tax_bracket": bracket,
                        "annual_taxable": annual,
                        "monthly_withholding": round(expected_tax, 2)
                    },
                    "rules_applied": ["BIR_TAX_BRACKETS_2024"]
                }
            })

        return examples

    def generate_codegen_examples(self) -> List[Dict[str, Any]]:
        """Generate examples for code-generator agent."""
        examples = []

        # Odoo model generation
        examples.append({
            "input": {
                "spec": {
                    "model": "bir.tax.calculation",
                    "fields": [
                        {"name": "employee_id", "type": "many2one", "relation": "hr.employee", "required": True},
                        {"name": "gross_salary", "type": "float", "required": True},
                        {"name": "sss_contribution", "type": "float", "computed": True},
                        {"name": "net_salary", "type": "float", "computed": True}
                    ],
                    "constraints": ["gross_salary >= 0"]
                },
                "target_framework": "odoo-18-ce"
            },
            "output": {
                "code": '''
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class BIRTaxCalculation(models.Model):
    _name = 'bir.tax.calculation'
    _description = 'BIR Tax Calculation'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
    )
    gross_salary = fields.Float(
        string='Gross Salary',
        required=True,
    )
    sss_contribution = fields.Float(
        string='SSS Contribution',
        compute='_compute_sss',
        store=True,
    )
    net_salary = fields.Float(
        string='Net Salary',
        compute='_compute_net_salary',
        store=True,
    )

    @api.depends('gross_salary')
    def _compute_sss(self):
        for record in self:
            # SSS computation logic
            record.sss_contribution = min(record.gross_salary * 0.045, 1350.00)

    @api.depends('gross_salary', 'sss_contribution')
    def _compute_net_salary(self):
        for record in self:
            record.net_salary = record.gross_salary - record.sss_contribution

    @api.constrains('gross_salary')
    def _check_gross_salary(self):
        for record in self:
            if record.gross_salary < 0:
                raise ValidationError(_('Gross salary cannot be negative.'))
''',
                "file_path": "models/bir_tax_calculation.py",
                "test_file": "tests/test_bir_tax_calculation.py"
            }
        })

        # FastAPI endpoint generation
        examples.append({
            "input": {
                "spec": {
                    "endpoint": "/api/v1/bir/calculate",
                    "method": "POST",
                    "request_schema": {
                        "gross_salary": "float",
                        "employee_id": "int"
                    },
                    "response_schema": {
                        "sss": "float",
                        "philhealth": "float",
                        "pagibig": "float",
                        "withholding_tax": "float",
                        "net_salary": "float"
                    }
                },
                "target_framework": "fastapi"
            },
            "output": {
                "code": '''
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import logging

router = APIRouter(prefix="/api/v1/bir", tags=["BIR Compliance"])
logger = logging.getLogger(__name__)


class TaxCalculationRequest(BaseModel):
    gross_salary: float = Field(..., ge=0, description="Monthly gross salary in PHP")
    employee_id: int = Field(..., gt=0, description="Employee ID")


class TaxCalculationResponse(BaseModel):
    sss: float
    philhealth: float
    pagibig: float
    withholding_tax: float
    net_salary: float


@router.post("/calculate", response_model=TaxCalculationResponse)
async def calculate_tax(request: TaxCalculationRequest):
    """Calculate Philippine tax deductions for an employee."""
    logger.info(f"Calculating tax for employee {request.employee_id}")

    # SSS (max 1350)
    sss = min(request.gross_salary * 0.045, 1350.00)

    # PhilHealth (2.5% employee share, max 1250)
    philhealth = min(request.gross_salary * 0.025, 1250.00)

    # PAGIBIG (2%, max 100)
    pagibig = min(request.gross_salary * 0.02, 100.00)

    # Withholding tax (simplified)
    taxable = request.gross_salary - sss - philhealth - pagibig
    annual_taxable = taxable * 12
    if annual_taxable <= 250000:
        annual_tax = 0
    elif annual_taxable <= 400000:
        annual_tax = (annual_taxable - 250000) * 0.15
    else:
        annual_tax = 22500 + (annual_taxable - 400000) * 0.20

    withholding_tax = annual_tax / 12

    return TaxCalculationResponse(
        sss=round(sss, 2),
        philhealth=round(philhealth, 2),
        pagibig=round(pagibig, 2),
        withholding_tax=round(withholding_tax, 2),
        net_salary=round(request.gross_salary - sss - philhealth - pagibig - withholding_tax, 2)
    )
''',
                "file_path": "api/v1/endpoints/bir.py"
            }
        })

        return examples

    def generate_sql_examples(self) -> List[Dict[str, Any]]:
        """Generate examples for sql-agent."""
        examples = []

        # Bronze to Silver transformation
        examples.append({
            "input": {
                "transformation": "bronze_to_silver",
                "source_table": "bronze.odoo_records",
                "target_table": "silver.invoices",
                "model_filter": "account.move"
            },
            "output": {
                "sql": '''
INSERT INTO silver.invoices (
    odoo_id, number, partner_id, partner_name,
    move_type, invoice_date, due_date,
    amount_untaxed, amount_tax, amount_total,
    state, synced_at
)
SELECT
    (odoo_data->>'id')::BIGINT,
    odoo_data->>'name',
    (odoo_data->'partner_id'->>0)::BIGINT,
    odoo_data->'partner_id'->>1,
    odoo_data->>'move_type',
    (odoo_data->>'invoice_date')::DATE,
    (odoo_data->>'invoice_date_due')::DATE,
    COALESCE((odoo_data->>'amount_untaxed')::DECIMAL, 0),
    COALESCE((odoo_data->>'amount_tax')::DECIMAL, 0),
    COALESCE((odoo_data->>'amount_total')::DECIMAL, 0),
    odoo_data->>'state',
    now()
FROM bronze.odoo_records
WHERE odoo_model = 'account.move'
  AND write_date > (SELECT COALESCE(MAX(synced_at), '1970-01-01') FROM silver.invoices)
ON CONFLICT (odoo_id) DO UPDATE SET
    number = EXCLUDED.number,
    partner_id = EXCLUDED.partner_id,
    partner_name = EXCLUDED.partner_name,
    amount_untaxed = EXCLUDED.amount_untaxed,
    amount_tax = EXCLUDED.amount_tax,
    amount_total = EXCLUDED.amount_total,
    state = EXCLUDED.state,
    updated_at = now(),
    synced_at = now();
''',
                "indexes": [
                    "CREATE INDEX idx_silver_invoices_partner ON silver.invoices(partner_id);",
                    "CREATE INDEX idx_silver_invoices_date ON silver.invoices(invoice_date);"
                ]
            }
        })

        # RLS policy generation
        examples.append({
            "input": {
                "table": "silver.payslips",
                "policies": [
                    {"role": "hr_manager", "operation": "ALL", "condition": "true"},
                    {"role": "employee", "operation": "SELECT", "condition": "own_records"}
                ]
            },
            "output": {
                "sql": '''
-- Enable RLS
ALTER TABLE silver.payslips ENABLE ROW LEVEL SECURITY;

-- HR Manager: Full access
CREATE POLICY hr_manager_full
ON silver.payslips FOR ALL
TO authenticated
USING (auth.jwt()->>'role' IN ('admin', 'hr_manager'))
WITH CHECK (auth.jwt()->>'role' IN ('admin', 'hr_manager'));

-- Employee: Own payslips only
CREATE POLICY employee_own_payslips
ON silver.payslips FOR SELECT
TO authenticated
USING (
    employee_id IN (
        SELECT odoo_id FROM silver.employees
        WHERE user_id = auth.uid()
    )
);
'''
            }
        })

        # Gold aggregation
        examples.append({
            "input": {
                "view": "gold.bir_1601c_summary",
                "source": "silver.payslips",
                "aggregation": "monthly_payroll_summary"
            },
            "output": {
                "sql": '''
CREATE MATERIALIZED VIEW gold.bir_1601c_summary AS
SELECT
    DATE_TRUNC('month', date_from)::DATE AS month,
    EXTRACT(YEAR FROM date_from) AS year,
    EXTRACT(MONTH FROM date_from) AS month_num,
    COUNT(DISTINCT employee_id) AS employee_count,
    SUM(gross_salary) AS total_compensation,
    SUM(sss_contribution) AS total_sss,
    SUM(philhealth) AS total_philhealth,
    SUM(pagibig) AS total_pagibig,
    SUM(withholding_tax) AS total_withholding_tax,
    SUM(net_salary) AS total_net_salary
FROM silver.payslips
WHERE state = 'done'
GROUP BY DATE_TRUNC('month', date_from),
         EXTRACT(YEAR FROM date_from),
         EXTRACT(MONTH FROM date_from);

CREATE UNIQUE INDEX idx_gold_1601c_pk ON gold.bir_1601c_summary(month);
'''
            }
        })

        return examples

    def generate_validation_examples(self) -> List[Dict[str, Any]]:
        """Generate examples for validation-agent."""
        examples = []

        # Test generation example
        examples.append({
            "input": {
                "code_path": "models/bir_tax_calculation.py",
                "target_coverage": 90,
                "test_types": ["unit", "integration"]
            },
            "output": {
                "tests": '''
import pytest
from decimal import Decimal

class TestBIRTaxCalculation:
    """Unit tests for BIR Tax Calculation."""

    @pytest.fixture
    def calculator(self):
        return BIRTaxCalculator()

    # SSS Tests
    def test_sss_minimum_bracket(self, calculator):
        """SSS for minimum salary (< ₱4,250) = ₱180."""
        result = calculator.calculate_sss(4000)
        assert result == 180.00

    def test_sss_maximum_bracket(self, calculator):
        """SSS for ₱30,000+ = ₱1,350 (max)."""
        result = calculator.calculate_sss(50000)
        assert result == 1350.00

    # PhilHealth Tests
    def test_philhealth_under_cap(self, calculator):
        """PhilHealth 2.5% for salary under cap."""
        result = calculator.calculate_philhealth(30000)
        assert result == 750.00

    def test_philhealth_capped(self, calculator):
        """PhilHealth capped at ₱1,250."""
        result = calculator.calculate_philhealth(100000)
        assert result == 1250.00

    # PAGIBIG Tests
    def test_pagibig_capped(self, calculator):
        """PAGIBIG capped at ₱100."""
        result = calculator.calculate_pagibig(10000)
        assert result == 100.00

    # Integration Tests
    def test_full_calculation(self, calculator):
        """Test complete tax calculation."""
        result = calculator.calculate_all(gross_salary=50000)

        assert result['sss'] == 1350.00
        assert result['philhealth'] == 1250.00
        assert result['pagibig'] == 100.00
        assert result['net_salary'] > 0
        assert result['net_salary'] < 50000

    def test_negative_salary_rejected(self, calculator):
        """Negative salary raises ValueError."""
        with pytest.raises(ValueError):
            calculator.calculate_all(gross_salary=-1000)
''',
                "coverage_estimate": 95,
                "test_count": 8
            }
        })

        # SLA validation example
        examples.append({
            "input": {
                "endpoint": "/api/v1/bir/calculate",
                "sla": {
                    "latency_p99": "2s",
                    "error_rate": "0.1%"
                }
            },
            "output": {
                "validation_result": {
                    "latency_p99": "1.2s",
                    "latency_passed": True,
                    "error_rate": "0.05%",
                    "error_rate_passed": True,
                    "overall_passed": True
                },
                "benchmark_code": '''
import time
import statistics

def benchmark_endpoint():
    latencies = []
    errors = 0
    total = 1000

    for _ in range(total):
        start = time.time()
        try:
            response = requests.post('/api/v1/bir/calculate', json={'gross_salary': 50000})
            if response.status_code >= 400:
                errors += 1
        except Exception:
            errors += 1
        latencies.append(time.time() - start)

    p99 = sorted(latencies)[int(0.99 * len(latencies))]
    error_rate = errors / total

    return {
        'latency_p99': p99,
        'error_rate': error_rate,
        'passed': p99 < 2.0 and error_rate < 0.001
    }
'''
            }
        })

        return examples

    def _generate_more_doc_parser_examples(self) -> List[Dict[str, Any]]:
        """Generate additional documentation parser examples."""
        examples = []

        # Supabase schema extraction
        examples.append({
            "input": """
Documentation: Supabase Bronze Layer Schema

CREATE TABLE bronze.webhook_log (
    id BIGSERIAL PRIMARY KEY,
    event_id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    source VARCHAR(50) NOT NULL DEFAULT 'odoo',
    model_name VARCHAR(255) NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('create', 'write', 'unlink')),
    payload JSONB NOT NULL,
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

Task: Extract table schema definition
""",
            "output": {
                "extracted_specs": {
                    "schema": "bronze",
                    "table": "webhook_log",
                    "columns": [
                        {"name": "id", "type": "BIGSERIAL", "constraints": ["PRIMARY KEY"]},
                        {"name": "event_id", "type": "UUID", "constraints": ["UNIQUE", "NOT NULL"], "default": "uuid_generate_v4()"},
                        {"name": "source", "type": "VARCHAR(50)", "constraints": ["NOT NULL"], "default": "'odoo'"},
                        {"name": "model_name", "type": "VARCHAR(255)", "constraints": ["NOT NULL"]},
                        {"name": "action", "type": "VARCHAR(20)", "constraints": ["NOT NULL", "CHECK (action IN ('create', 'write', 'unlink'))"]},
                        {"name": "payload", "type": "JSONB", "constraints": ["NOT NULL"]},
                        {"name": "processed_at", "type": "TIMESTAMPTZ"},
                        {"name": "created_at", "type": "TIMESTAMPTZ", "constraints": ["NOT NULL"], "default": "now()"}
                    ]
                },
                "confidence": "high"
            }
        })

        return examples

    def _save_dataset(self, agent_name: str, examples: List[Dict[str, Any]]):
        """Save dataset to JSONL file."""
        # Split into train/val/test (70/15/15)
        random.shuffle(examples)
        n = len(examples)
        train_end = int(0.7 * n)
        val_end = int(0.85 * n)

        train = examples[:train_end]
        val = examples[train_end:val_end]
        test = examples[val_end:]

        agent_dir = self.output_dir / agent_name
        agent_dir.mkdir(exist_ok=True)

        for split_name, split_data in [('train', train), ('val', val), ('test', test)]:
            if split_data:
                file_path = agent_dir / f'{split_name}.jsonl'
                with open(file_path, 'w') as f:
                    for example in split_data:
                        f.write(json.dumps(example) + '\n')


def main():
    parser = argparse.ArgumentParser(description='Generate fine-tuning datasets')
    parser.add_argument('--agent', type=str, help='Agent name to generate dataset for')
    parser.add_argument('--all', action='store_true', help='Generate datasets for all agents')
    parser.add_argument('--output', type=str, default='./datasets', help='Output directory')

    args = parser.parse_args()

    generator = DatasetGenerator(args.output)

    if args.all:
        generator.generate_all()
    elif args.agent:
        # Generate for specific agent
        method_map = {
            'documentation-parser': generator.generate_doc_parser_examples,
            'compliance-validator': generator.generate_compliance_examples,
            'code-generator': generator.generate_codegen_examples,
            'sql-agent': generator.generate_sql_examples,
            'validation-agent': generator.generate_validation_examples,
        }
        if args.agent in method_map:
            examples = method_map[args.agent]()
            generator._save_dataset(args.agent, examples)
            print(f"Generated {len(examples)} examples for {args.agent}")
        else:
            print(f"Unknown agent: {args.agent}")
            print(f"Available agents: {', '.join(method_map.keys())}")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
