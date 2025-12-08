# Data Engineering Workbench

A Databricks-style, self-hosted data engineering platform for the InsightPulseAI ecosystem.

## Overview

The Data Engineering Workbench serves as the central hub for building, testing, and deploying data pipelines. It sits at the heart of the development pipeline—after design (Figma) and planning (Spec Kit), and before production deployment.

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEVELOPMENT PIPELINE                         │
│                                                                 │
│   Design        Planning        Development      Deployment     │
│   ──────        ────────        ───────────      ──────────     │
│                                                                 │
│   Figma    →    Spec Kit   →   WORKBENCH   →   Production      │
│   Dev Mode      PRD/Tasks       Notebooks       Odoo/Superset   │
│                                 Pipelines                       │
│                                 Data Catalog                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features

- **Notebooks**: Interactive SQL and Python development environment
- **Pipelines**: Visual and code-based ETL/ELT workflow orchestration
- **Data Catalog**: Schema discovery, lineage tracking, and metadata management
- **Medallion Architecture**: Bronze → Silver → Gold data layers
- **Integrations**: Native connections to Odoo CE/OCA 18, Superset, OCR services, and AI agents

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA ENGINEERING WORKBENCH                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Frontend (Next.js)     API (FastAPI)      Execution Layer    │
│   ├── Dashboard          ├── Notebooks      ├── Jupyter        │
│   ├── Notebook Editor    ├── Pipelines      ├── DuckDB         │
│   ├── Pipeline Builder   ├── Catalog        ├── Temporal       │
│   └── Data Catalog       └── Integrations   └── Redis          │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                          STORAGE LAYER                          │
│                                                                 │
│   PostgreSQL (Medallion)     MinIO (Objects)    File Storage   │
│   ├── bronze.*               ├── documents      └── notebooks  │
│   ├── silver.*               ├── uploads                       │
│   ├── gold.*                 └── exports                       │
│   └── workbench.*                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Repository Structure

```
archi-agent-framework/
├── spec/                          # Spec Kit (governance + requirements)
│   └── data-engineering-workbench/
│       ├── constitution.md        # Non-negotiable principles
│       ├── prd.md                 # Product requirements
│       ├── plan.md                # Implementation plan
│       └── tasks.md               # Task breakdown
│
├── infra/                         # Infrastructure
│   ├── docker-compose.workbench.yml
│   ├── nginx/
│   │   └── workbench.conf
│   ├── postgres/
│   │   └── init/
│   ├── scripts/
│   │   ├── setup-workbench-droplet.sh
│   │   ├── enable-letsencrypt.sh
│   │   └── backup.sh
│   └── .env.workbench.example
│
├── apps/                          # Application code
│   └── workbench-api/
│       ├── app/
│       │   ├── api/v1/endpoints/
│       │   ├── core/
│       │   ├── models/
│       │   └── middleware/
│       ├── Dockerfile
│       └── requirements.txt
│
├── workflows/                     # n8n workflow templates
│   ├── month-end-finance.json
│   ├── ocr-to-odoo-expense.json
│   ├── agent-orchestrator.json
│   └── README.md
│
└── ops/                           # Operations documentation
    ├── monitoring.md
    ├── backups.md
    └── runbook-workbench-outage.md
```

## Quick Start

### Prerequisites

- DigitalOcean account with droplet(s)
- Domain configured (e.g., workbench.insightpulseai.net)
- SSH access to target droplet

### 1. Clone and Configure

```bash
# Clone repository
git clone https://github.com/your-org/archi-agent-framework.git
cd archi-agent-framework

# Copy and configure environment
cp infra/.env.workbench.example infra/.env.workbench
nano infra/.env.workbench  # Fill in your values
```

### 2. Deploy to Droplet

```bash
# SSH to your droplet
ssh root@YOUR_DROPLET_IP

# Run setup script
curl -fsSL https://raw.githubusercontent.com/your-org/archi-agent-framework/main/infra/scripts/setup-workbench-droplet.sh | bash

# Configure environment
nano /opt/workbench/infra/.env.workbench

# Enable SSL
bash /opt/workbench/infra/scripts/enable-letsencrypt.sh workbench.insightpulseai.net admin@insightpulseai.net

# Start services
cd /opt/workbench/infra
docker compose -f docker-compose.workbench.yml --env-file .env.workbench up -d
```

### 3. Verify Installation

```bash
# Check services
docker compose -f docker-compose.workbench.yml ps

# Test health endpoint
curl https://workbench.insightpulseai.net/health
```

## Integration Points

| Service | Endpoint | Purpose |
|---------|----------|---------|
| Odoo CE/OCA 18 | erp.insightpulseai.net | ERP data extraction |
| Superset | superset.insightpulseai.net | Dashboard integration |
| OCR Service | ocr.insightpulseai.net | Document extraction |
| MCP/Agents | mcp.insightpulseai.net | AI agent orchestration |
| n8n | n8n.insightpulseai.net | Workflow automation |

## Documentation

- **[Constitution](spec/data-engineering-workbench/constitution.md)** - Core principles and guardrails
- **[PRD](spec/data-engineering-workbench/prd.md)** - Product requirements and use cases
- **[Plan](spec/data-engineering-workbench/plan.md)** - Architecture and implementation phases
- **[Tasks](spec/data-engineering-workbench/tasks.md)** - Detailed task breakdown
- **[Monitoring](ops/monitoring.md)** - Metrics and alerting
- **[Backups](ops/backups.md)** - Backup and recovery procedures
- **[Runbook](ops/runbook-workbench-outage.md)** - Incident response

## Development

### Local Development

```bash
# Start dependencies
docker compose -f infra/docker-compose.workbench.yml up -d postgres redis minio

# Run API locally
cd apps/workbench-api
pip install -r requirements.txt
uvicorn app.main:app --reload

# Run frontend locally
cd apps/workbench-frontend
npm install
npm run dev
```

### Running Tests

```bash
cd apps/workbench-api
pytest tests/ -v
```

## License

Proprietary - InsightPulseAI

## Support

- **Slack**: #data-engineering
- **Issues**: GitHub Issues
- **Documentation**: This repository
