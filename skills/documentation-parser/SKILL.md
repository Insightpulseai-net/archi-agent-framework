---
name: documentation-parser
description: Recursively extract specifications from enterprise documentation (Odoo 18 CE, Microsoft Learn, Supabase, GitHub, SAP Help). Identifies APIs, schemas, compliance rules, and creates glossaries. Use when analyzing documentation or building architectural blueprints from official sources.
license: Apache-2.0
metadata:
  author: insightpulseai
  version: "1.0"
  domain: documentation
  stack: ["odoo-18-ce", "supabase", "microsoft-learn", "sap-help", "github"]
---

# Documentation Parser Skill

Extract specifications from enterprise documentation recursively.

## Purpose

This agent specializes in reading and extracting structured specifications from official enterprise documentation. It creates machine-readable artifacts from human-readable docs.

## How to Use

1. **Provide documentation source** (URL or content)
2. **Set extraction scope** (APIs, schemas, compliance, terms)
3. **Agent extracts specs** with confidence levels
4. **Surfaces conflicts** between documents
5. **Creates glossary** of domain-specific terms

## Supported Documentation Sources

| Source | URL Pattern | Extraction Types |
|--------|-------------|------------------|
| Odoo 18 CE | `odoo.com/documentation/18.0/` | Models, APIs, Workflows |
| Microsoft Learn | `learn.microsoft.com/` | Architecture, APIs, Configs |
| Supabase | `supabase.com/docs/` | Schemas, RLS, Functions |
| SAP Help | `help.sap.com/docs/` | Processes, Data Models |
| GitHub | `github.com/*/README.md` | Code patterns, Examples |

## Extraction Capabilities

### Database Schemas
- Table names, columns, data types, constraints
- Foreign keys, indexes, sequences
- Example: Extract from Supabase bronze/silver/gold schema

### API Endpoints
- Route definitions, HTTP methods, parameters
- Request/response formats, error codes
- Example: Extract Odoo webhook endpoints, Supabase RPC definitions

### Compliance Rules
- BIR tax form requirements (1700, 1601-C, 2550-Q)
- Deduction tables and validation rules
- SoD (Segregation of Duties) matrices

### Technical Glossary
- Domain-specific terminology
- Acronyms with definitions
- Related concepts

## Example Inputs & Outputs

### Input
```json
{
  "source": "Supabase Row Level Security guide",
  "extraction_scope": ["rls_policies", "role_definitions"],
  "confidence_threshold": "high"
}
```

### Output
```json
{
  "extractions": [
    {
      "type": "rls_policy",
      "table": "silver_invoices",
      "role": "approver",
      "condition": "approval_state = 'pending'",
      "confidence": "high",
      "source_url": "https://supabase.com/docs/guides/database/postgres/row-level-security"
    }
  ],
  "glossary": {
    "RLS": "Row Level Security - Postgres feature for row-level access control",
    "Policy": "SQL rule that filters data per user role"
  },
  "conflicts": [],
  "related_docs": [
    "https://supabase.com/docs/guides/database/postgres/row-level-security"
  ]
}
```

## Edge Cases

| Scenario | Handling |
|----------|----------|
| Conflicting information across versions | Flag with confidence levels, cite both sources |
| Missing documentation | Recommend alternative sources, mark as "incomplete" |
| Proprietary formats (PDF, DOCX) | Extract what's accessible; note limitations |
| Language barriers | Extract with note of source language |
| Deprecated APIs | Flag as deprecated, suggest alternatives |

## Skill Boundaries

### What This Skill CAN Do
- Extract explicit specifications from documentation
- Create structured JSON from unstructured text
- Identify APIs, schemas, workflows, and rules
- Build glossaries of domain terms
- Flag conflicts and missing information

### What This Skill CANNOT Do
- Generate code (use `code-generator` skill)
- Validate compliance (use `compliance-validator` skill)
- Execute SQL queries (use `sql-agent` skill)
- Deploy systems (use `deployment-orchestrator` skill)

## Rules

- Only extract explicit specifications (no inferences)
- Mark confidence level (high/medium/low) for each extraction
- Preserve exact field names, types, and syntax
- Surface conflicting information between documents
- Always cite source URL for each extraction
- **DO NOT** hallucinate specifications not found in source
