# InsightPulseAI Agent Skills

This directory contains bounded AI agent skills following the [Anthropic Agent Skills Specification](https://agentskills.io/specification).

## Overview

Each skill defines a specialized agent with:
- **Clear purpose**: What the agent does
- **Skill boundaries**: What it CAN and CANNOT do
- **Examples**: Input/output demonstrations
- **Rules**: Guardrails and constraints

## Available Skills

| Skill | Domain | Purpose |
|-------|--------|---------|
| [documentation-parser](./documentation-parser/SKILL.md) | Documentation | Extract specs from Odoo, Supabase, SAP, Microsoft docs |
| [compliance-validator](./compliance-validator/SKILL.md) | Compliance | Validate against BIR 2024, SSS, PhilHealth, PAGIBIG |
| [code-generator](./code-generator/SKILL.md) | Code Generation | Generate Odoo, FastAPI, React, SQL from specs |
| [sql-agent](./sql-agent/SKILL.md) | Database | Write bronze/silver/gold transformations, RLS policies |
| [validation-agent](./validation-agent/SKILL.md) | Testing | Generate tests, check coverage, validate SLAs |
| [deployment-orchestrator](./deployment-orchestrator/SKILL.md) | Deployment | Manage dev → staging → production pipeline |

## Agent Workflow

```
┌─────────────────────┐
│ documentation-parser │
│   (Extract specs)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ compliance-validator │
│   (Validate rules)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐     ┌─────────────────────┐
│   code-generator    │────▶│     sql-agent       │
│  (Generate code)    │     │  (Generate SQL)     │
└──────────┬──────────┘     └──────────┬──────────┘
           │                           │
           └───────────┬───────────────┘
                       ▼
           ┌─────────────────────┐
           │  validation-agent   │
           │   (Run tests)       │
           └──────────┬──────────┘
                      │
                      ▼
           ┌─────────────────────┐
           │deployment-orchestrator│
           │   (Deploy)          │
           └─────────────────────┘
```

## Usage

### With Claude Code
```bash
# Skills are automatically loaded when Claude Code runs in this directory
# Reference skills in prompts:
# "Use the compliance-validator skill to validate this payslip"
# "Use the sql-agent skill to create RLS policies for invoices"
```

### With Anthropic API
```python
from anthropic import Anthropic

client = Anthropic()

# Load skill as system prompt
with open("skills/compliance-validator/SKILL.md") as f:
    skill_prompt = f.read()

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    system=skill_prompt,
    messages=[
        {"role": "user", "content": "Validate this payslip: gross=50000, sss=0"}
    ]
)
```

## Directory Structure

```
skills/
├── README.md                          # This file
├── documentation-parser/
│   ├── SKILL.md                       # Skill definition
│   ├── scripts/                       # Optional helper scripts
│   └── references/                    # Reference documents
├── compliance-validator/
│   ├── SKILL.md
│   ├── scripts/
│   └── references/
│       ├── BIR_2024_TABLES.md
│       └── SSS_PAYROLL.md
├── code-generator/
│   ├── SKILL.md
│   ├── scripts/
│   └── templates/                     # Code templates
├── sql-agent/
│   ├── SKILL.md
│   ├── scripts/
│   └── references/
├── validation-agent/
│   ├── SKILL.md
│   └── scripts/
└── deployment-orchestrator/
    ├── SKILL.md
    └── scripts/
```

## Core Principles

These skills follow the InsightPulseAI 80/20 rule:

1. **Odoo 18 CE First (80%)**: Leverage native modules
2. **OCA Modules (15%)**: Use community add-ons
3. **Custom Code (5%)**: Only for genuine gaps

## Philippine Compliance

All skills are designed for Philippine regulatory compliance:

- **BIR**: Forms 1700, 1601-C, 2550-Q, all 36 eBIR forms
- **SSS**: 2024 contribution table
- **PhilHealth**: 2.5% employee share, ₱1,250 cap
- **PAGIBIG**: 2% employee share, ₱100 cap
- **13th Month**: Mandatory, due December 24

## Contributing

When adding new skills:

1. Create directory: `skills/{skill-name}/`
2. Create `SKILL.md` with YAML frontmatter
3. Define clear boundaries (CAN/CANNOT)
4. Include examples with input/output
5. Add to this README

## License

Apache-2.0
