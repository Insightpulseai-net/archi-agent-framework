# Data Engineering Workbench - Constitution

## Document Control
- **Version**: 1.0.0
- **Status**: Active
- **Last Updated**: 2025-12-08
- **Owner**: InsightPulseAI Platform Team

---

## 1. Purpose & Scope

This constitution defines the non-negotiable principles, guardrails, and governance rules for the **Data Engineering Workbench** - a Databricks-style development environment that serves as the central hub for data transformations, pipeline orchestration, and analytics automation within the InsightPulseAI ecosystem.

### 1.1 Mission Statement

> To provide a self-hosted, enterprise-grade data engineering platform that bridges the gap between design, development, and deployment—enabling finance, analytics, and AI teams to build, test, and deploy data pipelines with full observability and governance.

### 1.2 Scope

This workbench covers:
- **Data Pipeline Development**: ETL/ELT workflows, transformations, and data quality checks
- **Notebook Environment**: Interactive SQL, Python, and dbt development
- **Job Orchestration**: Scheduling, dependency management, and workflow automation
- **Data Catalog**: Schema discovery, lineage tracking, and metadata management
- **Integration Hub**: Connections to Odoo, Superset, OCR services, and AI agents

---

## 2. Non-Negotiable Principles

### 2.1 Self-Hosted Only
```
RULE: No SaaS dependencies for core workbench functionality.
```
- All components must run on DigitalOcean infrastructure
- No data leaves the fin-workspace environment without explicit approval
- External integrations (Figma, GitHub) are read-only or webhook-based

### 2.2 No Secrets in Git
```
RULE: Zero plaintext secrets in any repository.
```
- All credentials via `.env` files (not committed)
- Secrets mounted as Docker secrets or environment variables
- API keys rotated quarterly minimum
- Audit log for all secret access

### 2.3 Spec-Driven Development (SDD)
```
RULE: No code without specs. No deployment without plan.
```
- Every feature requires PRD entry before implementation
- Every pipeline requires documented data contract
- Every change requires task reference in `tasks.md`

### 2.4 Replayable & Observable
```
RULE: Every pipeline run must be reproducible and traceable.
```
- All job executions logged with full context
- Data lineage tracked from source to destination
- Rollback capability for any transformation
- Time-travel for data states (minimum 7 days)

### 2.5 Finance-Critical Audit Trail
```
RULE: Finance-related data flows require complete audit logs.
```
- Who ran the job, when, with what parameters
- Data volumes processed and affected rows
- Approval chain for production deployments
- Retention: 7 years for financial audit trails

---

## 3. Architecture Constraints

### 3.1 Technology Stack
| Layer | Technology | Rationale |
|-------|------------|-----------|
| Compute | Docker containers on DO Droplets | Self-hosted, reproducible |
| Database | PostgreSQL 15+ | Proven, ACID-compliant |
| Query Engine | DuckDB / Trino | Fast OLAP, low resource |
| Orchestration | n8n + Apache Airflow Lite | Visual + code-based |
| Notebooks | JupyterHub / VS Code Server | Industry standard |
| Frontend | Next.js + React + Tailwind | Consistent with Scout |
| API | FastAPI / Express | High performance |

### 3.2 Data Architecture
```
Bronze (Raw) → Silver (Cleaned) → Gold (Business-Ready)
```
- **Bronze**: Raw ingestion, immutable, partitioned by date
- **Silver**: Validated, deduplicated, typed
- **Gold**: Business aggregates, SCD Type 2 where applicable

### 3.3 Integration Boundaries
```
┌─────────────────────────────────────────────────────────────┐
│                    TRUSTED ZONE (Internal)                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │  Odoo   │  │Superset │  │   OCR   │  │   MCP   │       │
│  │  CE/18  │  │Analytics│  │ Service │  │ Agents  │       │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘       │
│       │            │            │            │             │
│       └────────────┴────────────┴────────────┘             │
│                         │                                   │
│              ┌──────────┴──────────┐                       │
│              │  Data Engineering   │                       │
│              │     Workbench       │                       │
│              └──────────┬──────────┘                       │
│                         │                                   │
└─────────────────────────┼───────────────────────────────────┘
                          │
              ┌───────────┴───────────┐
              │    EXTERNAL ZONE      │
              │  (Read-only / Hooks)  │
              │  ┌──────┐  ┌───────┐  │
              │  │Figma │  │GitHub │  │
              │  └──────┘  └───────┘  │
              └───────────────────────┘
```

---

## 4. Security Policies

### 4.1 Authentication
- All workbench access requires authentication
- SSO integration with existing auth.insightpulseai.net
- Session timeout: 8 hours (configurable)
- MFA required for production data access

### 4.2 Authorization
| Role | Permissions |
|------|-------------|
| Viewer | Read notebooks, view job history |
| Developer | Create/edit notebooks, run jobs in sandbox |
| Engineer | Deploy to staging, manage connections |
| Admin | Production deploy, secret management |

### 4.3 Network Security
- All endpoints behind nginx reverse proxy
- TLS 1.3 minimum
- Rate limiting: 100 req/min per user
- IP allowlist for admin functions

---

## 5. Coding Standards

### 5.1 SQL
- Use CTEs over subqueries
- Explicit column names (no `SELECT *` in production)
- Date columns: `_at` suffix for timestamps, `_date` for dates
- Consistent naming: `snake_case` for all identifiers

### 5.2 Python
- Black formatter, isort for imports
- Type hints required for all functions
- Docstrings for all public methods
- No bare `except` clauses

### 5.3 Pipeline Code
- Idempotent by default (re-runnable without side effects)
- Explicit dependencies declared
- Timeout on all external calls
- Graceful degradation for non-critical steps

---

## 6. Testing Requirements

### 6.1 Data Quality Tests
- Schema validation on all ingestion
- Null checks on required fields
- Referential integrity tests for joins
- Volume anomaly detection (±20% threshold)

### 6.2 Pipeline Tests
- Unit tests for transformation logic
- Integration tests for end-to-end flows
- Smoke tests before production deploy
- Rollback tests for critical pipelines

### 6.3 Coverage Requirements
| Type | Minimum Coverage |
|------|-----------------|
| Transformation logic | 80% |
| API endpoints | 90% |
| Critical finance flows | 100% |

---

## 7. Operational Guardrails

### 7.1 Change Management
- All production changes via PR
- Minimum 1 reviewer for code
- Minimum 2 reviewers for finance pipelines
- No direct production edits

### 7.2 Incident Response
- P1 (Data Loss Risk): 15-minute response
- P2 (Job Failure): 1-hour response
- P3 (Performance): 4-hour response
- P4 (Enhancement): Next sprint

### 7.3 Data Retention
| Data Type | Retention | Archive |
|-----------|-----------|---------|
| Bronze | 90 days | Glacier after 30 |
| Silver | 1 year | Glacier after 90 |
| Gold | 7 years | Per compliance |
| Logs | 2 years | Compressed after 30 |

---

## 8. Compliance & Governance

### 8.1 Data Classification
- **Public**: Aggregated reports, dashboards
- **Internal**: Operational data, non-PII
- **Confidential**: Financial records, vendor data
- **Restricted**: PII, credentials, API keys

### 8.2 Audit Requirements
- Log all data access for Confidential+
- Quarterly access reviews
- Annual compliance audit
- Immediate notification of breaches

---

## 9. Amendment Process

Changes to this constitution require:
1. Written proposal with rationale
2. Review by Platform Team
3. 72-hour comment period
4. Approval by technical lead + finance lead
5. Version increment and changelog entry

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| SDD | Spec-Driven Development |
| ETL | Extract, Transform, Load |
| SCD | Slowly Changing Dimension |
| OLAP | Online Analytical Processing |
| MCP | Multi-agent Coordination Protocol |
