---
name: compliance-validator
description: Validate business logic against Philippine regulations (BIR Forms 1700/1601-C/2550-Q, SSS/PhilHealth/PAGIBIG deductions, SoD rules). Use when processing payroll, invoices, journal entries, or designing approval workflows. Ensures 100% compliance with 2024 PH tax requirements.
license: Apache-2.0
metadata:
  author: insightpulseai
  version: "1.0"
  domain: compliance
  jurisdiction: philippines
  tax_year: 2024
---

# Compliance Validator Skill

Validate business transactions against Philippine tax and labor regulations.

## Purpose

This agent ensures all financial transactions comply with Bureau of Internal Revenue (BIR) requirements, SSS/PhilHealth/PAGIBIG deduction tables, and Segregation of Duties (SoD) controls.

## How to Use

1. **Provide transaction data** (invoice, payslip, journal entry)
2. **Specify transaction type** (invoice, payment, payroll)
3. **Agent validates** against BIR tables and rules
4. **Returns compliance status** with violations and corrections

## Validation Rules (2024)

### BIR Form 1700 (Annual Income Tax Return)
- Gross income must equal sum of all invoices
- Withholding tax must equal sum of 1601-C deductions
- Formula: `Net taxable income = Gross - Withholding`
- Filing deadline: April 15 (following tax year)

### BIR Form 1601-C (Monthly Withholding Tax)
- Computation: Based on graduated rates
- Filed monthly, consolidated annually
- Required when employee count > 0
- Deadline: 10th of following month

### BIR Form 2550-Q (Quarterly VAT Return)
- VAT rate: 12% on taxable sales
- Output VAT - Input VAT = Payable VAT
- Filed quarterly (Jan-Mar, Apr-Jun, Jul-Sep, Oct-Dec)
- Deadline: 25th of month following quarter end

### 2024 Income Tax Brackets (Graduated Rates)

| Annual Income | Tax Rate |
|---------------|----------|
| ≤ ₱250,000 | 0% (exempt) |
| ₱250,001 - ₱400,000 | 15% of excess over ₱250,000 |
| ₱400,001 - ₱800,000 | ₱22,500 + 20% of excess over ₱400,000 |
| ₱800,001 - ₱2,000,000 | ₱102,500 + 25% of excess over ₱800,000 |
| ₱2,000,001 - ₱8,000,000 | ₱402,500 + 30% of excess over ₱2,000,000 |
| > ₱8,000,000 | ₱2,202,500 + 35% of excess over ₱8,000,000 |

### Payroll Deductions (Mandatory)

| Deduction | Rate | Cap |
|-----------|------|-----|
| SSS | Variable by bracket | See SSS 2024 table |
| PhilHealth | 5% (employee share: 2.5%) | Max ₱5,000/month total |
| PAGIBIG | 2% (employee share: 1-2%) | Max ₱200/month total |

### SSS Contribution Table 2024 (Employee Share)

| Monthly Salary Credit | Employee Share |
|----------------------|----------------|
| ₱4,000 - ₱4,249 | ₱180 |
| ₱4,250 - ₱4,749 | ₱202.50 |
| ₱10,000 - ₱10,749 | ₱450 |
| ₱15,000 - ₱15,749 | ₱675 |
| ₱20,000 - ₱20,249 | ₱900 |
| ₱25,000 - ₱29,999 | ₱1,125 |
| ₱30,000+ | ₱1,350 (max) |

### Segregation of Duties (SoD)

| Role A | Role B | Conflict |
|--------|--------|----------|
| Invoice Creator | Invoice Approver | YES |
| Payment Preparer | Payment Approver | YES |
| GL Poster | Invoice/Payment Approver | YES |
| Expense Submitter | Expense Approver | YES |

## Example Validation

### Input
```json
{
  "transaction_type": "payslip",
  "employee_id": "EMP-001",
  "gross_salary": 50000,
  "sss_contribution": 0,
  "philhealth": 1200,
  "pagibig": 50,
  "withholding_tax": 5000
}
```

### Output
```json
{
  "compliant": false,
  "violations": [
    {
      "rule": "SSS_CONTRIBUTION_REQUIRED",
      "field": "sss_contribution",
      "expected": 1350,
      "actual": 0,
      "severity": "critical",
      "reference": "SSS Contribution Table 2024"
    },
    {
      "rule": "PHILHEALTH_UNDERPAID",
      "field": "philhealth",
      "expected": 1250,
      "actual": 1200,
      "severity": "warning",
      "reference": "PhilHealth Rate 2024 (2.5% employee share)"
    },
    {
      "rule": "PAGIBIG_UNDERPAID",
      "field": "pagibig",
      "expected": 100,
      "actual": 50,
      "severity": "warning",
      "reference": "PAGIBIG Contribution Table 2024"
    }
  ],
  "corrected_values": {
    "sss_contribution": 1350,
    "philhealth": 1250,
    "pagibig": 100,
    "total_deductions": 7700,
    "net_salary": 42300
  },
  "audit_trail": {
    "validated_at": "2024-12-30T10:00:00Z",
    "rules_applied": ["SSS_2024", "PHILHEALTH_2024", "PAGIBIG_2024", "BIR_1601C"]
  }
}
```

## Edge Cases

| Scenario | Handling |
|----------|----------|
| Senior citizen (age 65+) | Additional ₱25,000 exemption |
| PWD (Persons with Disability) | Additional ₱25,000 exemption |
| Minimum wage earner | Exempt from withholding tax |
| 13th month bonus | Non-taxable if ≤ ₱90,000 |
| Overtime pay | Taxable, include in gross |
| Separation pay | Non-taxable if involuntary |

## Skill Boundaries

### What This Skill CAN Do
- Validate transactions against BIR rules
- Calculate correct SSS/PhilHealth/PAGIBIG contributions
- Check SoD conflicts
- Compute withholding tax
- Flag violations with corrections

### What This Skill CANNOT Do
- Extract specifications from docs (use `documentation-parser`)
- Generate code (use `code-generator`)
- Write SQL queries (use `sql-agent`)
- Deploy systems (use `deployment-orchestrator`)

## Rules

- Use only 2024 official BIR tables
- Flag all deviations with specific corrections
- Show calculation steps for transparency
- Create audit trail for every validation
- **DO NOT** override mandatory requirements
- **DO NOT** accept custom deduction rates outside legal bounds
