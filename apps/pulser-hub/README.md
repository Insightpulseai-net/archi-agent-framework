# Pulser-Hub

ChatGPT-compatible AI Agent for Docs2Code Pipeline Control.

## Overview

Pulser-Hub is a FastAPI backend that enables natural language control of the InsightPulseAI Docs2Code pipeline through ChatGPT Actions. It integrates with:

- **Databricks** - For notebook execution and pipeline orchestration
- **GitHub App** - For code commits and pull requests
- **Odoo 18** - For ERP module deployment
- **Supabase** - For vector storage and compliance data

## Features

### Pipeline Control
Execute the complete Docs2Code pipeline or individual stages:
- `run_full_pipeline` - Full 6-notebook sequence (~90 min)
- `run_ingestion` - Document ingestion to RAG (~30 min)
- `run_analysis` - Gap analysis between docs and implementation (~15 min)
- `run_generation` - Odoo module code generation (~20 min)
- `run_compliance` - BIR compliance verification (~10 min)
- `run_deployment` - Deploy to staging/production (~15 min)

### BIR Compliance
Monitor and verify compliance for all 36 Philippine BIR tax forms:
- Income Tax: 1700, 1701, 1702, 1702Q, etc.
- Withholding Tax: 1601-C, 1601-E, 1604-CF, etc.
- VAT: 2550-M, 2550-Q, 2551-M, etc.
- Excise, Documentary Stamp, and Others

### GitHub Integration
- Commit generated code to branches
- Create pull requests with descriptions
- Monitor CI/CD workflow status
- Webhook handlers for automated triggers

### Odoo Deployment
Deploy generated modules to Odoo 18 instances:
- **Staging**: https://staging.erp.insightpulseai.net
- **Production**: https://erp.insightpulseai.net

## Quick Start

### Prerequisites
- Python 3.11+
- Docker (optional)
- GitHub App credentials
- Databricks workspace
- Odoo instance

### Local Development

```bash
# Clone the repository
cd apps/pulser-hub

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your credentials

# Run the server
uvicorn api.main:app --reload --port 8000
```

### Docker

```bash
# Build image
docker build -t pulser-hub:latest .

# Run container
docker run -p 8000:8000 \
  -e GITHUB_APP_ID=2191216 \
  -e GITHUB_CLIENT_ID=Iv23liwGL7fnYySPPAjS \
  -e GITHUB_PRIVATE_KEY="$(cat private-key.pem)" \
  pulser-hub:latest
```

### Azure Container Instances

```bash
# Deploy to Azure
az container create \
  --resource-group pulser-rg \
  --name pulser-hub \
  --image pulser-hub:latest \
  --dns-name-label pulser-hub \
  --ports 8000 \
  --environment-variables \
    GITHUB_APP_ID=2191216 \
    GITHUB_CLIENT_ID=Iv23liwGL7fnYySPPAjS
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/pipeline/run` | POST | Execute pipeline action |
| `/pipeline/status/{run_id}` | GET | Get pipeline status |
| `/compliance/status/{form_number}` | GET | Get BIR form compliance |
| `/compliance/summary` | GET | Get all forms summary |
| `/github/commit` | POST | Commit code to GitHub |
| `/github/status` | GET | Get GitHub App status |
| `/odoo/deploy` | POST | Deploy module to Odoo |
| `/odoo/status/{deployment_id}` | GET | Get deployment status |
| `/chatgpt/function-call` | POST | ChatGPT Actions entry point |
| `/webhook/github` | POST | GitHub webhook handler |

## ChatGPT Integration

### Setting Up ChatGPT Actions

1. Go to [ChatGPT Apps](https://chatgpt.com/apps?c=productivity)
2. Create new GPT or edit existing
3. Add Action with OpenAPI schema from `/schemas/openai-actions.json`
4. Set authentication to API Key
5. Use system prompt from `/prompts/system-prompt.md`

### Example Conversations

**Running the pipeline:**
```
User: "Run the Docs2Code pipeline"
Pulser-Hub: I'll start the full Docs2Code pipeline. This will execute:
1. Ingestion (30 min)
2. Analysis (15 min)
3. Generation (20 min)
4. Compliance (10 min)
5. Deployment (15 min)

Pipeline started! Run ID: run-20251231120000
Estimated completion: 90 minutes
```

**Checking compliance:**
```
User: "What's the status of BIR Form 1700?"
Pulser-Hub: BIR Form 1700 Compliance Status:
✅ Fields Covered: 28/28 (100%)
✅ 2024 Tax Rates: Applied
✅ Audit Trails: Enabled
✅ e-Filing Ready: Yes

Overall Status: COMPLIANT (100%)
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        ChatGPT                              │
│                    (Natural Language)                       │
└─────────────────────────┬───────────────────────────────────┘
                          │ OpenAI Actions API
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      Pulser-Hub                             │
│                   (FastAPI Backend)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Pipeline   │  │ Compliance  │  │  GitHub/Odoo        │  │
│  │  Control    │  │ Monitor     │  │  Integration        │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
└─────────┼────────────────┼─────────────────────┼────────────┘
          │                │                     │
          ▼                ▼                     ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────────────────┐
│   Databricks    │ │  Supabase   │ │  GitHub    │   Odoo    │
│   (Notebooks)   │ │  (pgvector) │ │  App       │   18 CE   │
└─────────────────┘ └─────────────┘ └─────────────────────────┘
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_APP_ID` | GitHub App ID | `2191216` |
| `GITHUB_CLIENT_ID` | GitHub App Client ID | `Iv23liwGL7fnYySPPAjS` |
| `GITHUB_PRIVATE_KEY` | GitHub App private key PEM | - |
| `GITHUB_WEBHOOK_SECRET` | Webhook signature secret | - |
| `DATABRICKS_WORKSPACE_URL` | Databricks workspace URL | - |
| `DATABRICKS_TOKEN` | Databricks access token | - |
| `DATABRICKS_CLUSTER_ID` | Default cluster ID | - |
| `SUPABASE_URL` | Supabase project URL | - |
| `SUPABASE_KEY` | Supabase service key | - |
| `ODOO_STAGING_API_KEY` | Staging Odoo API key | - |
| `ODOO_PRODUCTION_API_KEY` | Production Odoo API key | - |

## Core Principles

1. **80/20 Rule**: Odoo 18 CE native (80%), OCA modules (15%), custom code (5%)
2. **Compliance First**: BIR compliance, audit trails, separation of duties
3. **Deterministic Quality**: All code validated before deployment
4. **Transparency**: Clear explanations of all actions

## GitHub App Configuration

- **App ID**: 2191216
- **Client ID**: Iv23liwGL7fnYySPPAjS
- **Repository**: Insightpulseai-net/pulser-agent-framework

### Required Permissions
- Repository: Read & Write
- Pull Requests: Read & Write
- Webhooks: Read
- Workflows: Read & Write

## License

Copyright © 2024-2025 InsightPulseAI. All rights reserved.
