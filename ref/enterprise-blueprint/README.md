# Enterprise Blueprint Reference

**Source**: `/Users/tbwa/Downloads/insightpulse-enterprise-v2.zip`
**Last Updated**: 2025-12-09
**Status**: Reference-only (Phase 3 target)

---

## Purpose

This directory contains **reference materials** from the complete InsightPulse AI Enterprise platform blueprint. It is **NOT** part of the current Phase 1 MVP implementation.

**Do NOT merge this code directly into the main codebase.**

Use it as a **reference guide** for:
- Enterprise architecture patterns
- Security compliance checklists (SOC 2, ISO 27001)
- Complete data model schemas
- Fortune 500-grade infrastructure patterns

---

## Contents

### 📁 `security/`
- **`SECURITY_CHECKLIST.md`** - 74 SOC 2/ISO 27001 controls
  - Authentication & Authorization (12 controls)
  - Data Protection & Encryption (8 controls)
  - Network Security (10 controls)
  - Application Security (14 controls)
  - Infrastructure Security (8 controls)
  - Monitoring & Logging (9 controls)
  - Incident Response (7 controls)
  - Compliance & Governance (6 controls)

### 📁 `data-models/`
- **`complete-schema.sql`** - Full enterprise PostgreSQL schema
  - Multi-tenant architecture with RLS
  - 30+ tables across all domains
  - Finance, HR, Procurement, Analytics
  - Vector embeddings (pgvector)
  - Audit logging and versioning

### 📁 `docs/`
- **`ARCHITECTURE.md`** - Master architecture documentation
  - Executive summary with cost comparison ($3.1M → $17K/year)
  - Complete architecture stack (7 layers)
  - Enterprise application replacement mapping
  - Infrastructure deployment patterns
  - AI/ML platform components
  - Data engineering pipelines

---

## Enterprise Blueprint Overview

### Cost Comparison

| Enterprise Software | Annual Cost | InsightPulse Alternative | Cost |
|---------------------|-------------|--------------------------|------|
| SAP S/4HANA | $500,000 | Odoo 18 CE + ipai_* | $0 |
| SAP Concur | $150,000 | ipai_travel_expense | $0 |
| SAP Ariba | $120,000 | ipai_procurement | $0 |
| SAP SuccessFactors | $100,000 | ipai_hire_to_retire | $0 |
| Microsoft Dynamics 365 | $200,000 | Odoo 18 CE | $0 |
| Microsoft Power BI | $50,000 | Apache Superset | $0 |
| Databricks | $500,000 | Self-hosted Spark + MLflow | $10,000 |
| Snowflake | $200,000 | ClickHouse + DuckDB | $2,000 |
| Salesforce | $200,000 | Odoo CRM + ipai_crm | $0 |
| Oracle EBS | $400,000 | Odoo 18 CE | $0 |
| **TOTAL** | **$3,120,000** | **InsightPulse AI** | **$17,000** |

**ROI: 18,353%** | **Savings: $3,103,000/year**

### Architecture Layers

1. **Presentation Layer**: Odoo Web UI, React Portal, Mobile PWA, Slack/Teams/WhatsApp bots
2. **API Gateway Layer**: Traefik (reverse proxy + TLS 1.3 + WAF), Kong, GraphQL, REST, gRPC
3. **Application Layer**: Odoo 18 CE, n8n, AI Agents, Data Engine, OCR, Email, Notifications, Storage
4. **Data Engineering Layer**: Spark, Airflow, dbt, Great Expectations, Kafka, Debezium, Feast
5. **AI/ML Platform Layer**: Ollama, MLflow, LangChain, CrewAI, Chroma, Label Studio, AutoGluon
6. **Data Storage Layer**: PostgreSQL 15, ClickHouse, DuckDB, MinIO S3, Redis, Elasticsearch
7. **Infrastructure Layer**: Docker Swarm/Kubernetes, Traefik, Prometheus, Grafana, Vault, Consul

### Key Technologies

**Data Engineering**:
- Apache Spark 3.5 (Databricks parity)
- Apache Airflow 2.8 (orchestration)
- dbt Core (transformations)
- Great Expectations (quality)
- Apache Kafka (streaming)
- Debezium (CDC)

**AI/ML**:
- Ollama (LLM runtime - llama3.2)
- MLflow (experiment tracking)
- LangChain (RAG pipeline)
- CrewAI (multi-agent orchestration)
- Chroma + pgvector (vector DB)
- AutoGluon (AutoML)

**Security**:
- TLS 1.3 + WAF + OAuth2 Proxy
- HashiCorp Vault (secrets)
- Immutable audit logging
- SOC 2 Type II controls
- ISO 27001 compliance

---

## Integration Strategy

### ❌ What NOT to Do

- **DO NOT** copy-paste enterprise code into Phase 1 MVP
- **DO NOT** enable enterprise features before Phase 3
- **DO NOT** deploy enterprise infrastructure for MVP
- **DO NOT** deviate from canonical schema (DATA_MODEL.md)

### ✅ What TO Do

1. **Reference for Patterns**:
   - Use `SECURITY_CHECKLIST.md` to guide security implementation
   - Reference `complete-schema.sql` for advanced patterns (triggers, functions, views)
   - Study `ARCHITECTURE.md` for infrastructure design decisions

2. **Cross-Check Canonical Schema**:
   - Compare `complete-schema.sql` with `packages/db/sql/*.sql`
   - Identify patterns to adopt (e.g., audit triggers, RLS policies)
   - Ensure consistency with canonical types (timestamptz, uuid, jsonb, text enums)

3. **Feature Flag Alignment**:
   - Map enterprise features to `docs/FEATURE_FLAGS.md`
   - Ensure enterprise flags remain disabled until Phase 3
   - Document which enterprise features align with future roadmap

4. **Security Hardening**:
   - Implement relevant SOC 2 controls from checklist
   - Add security patterns from `security_module.py` (e.g., encryption helpers)
   - Create `docs/SECURITY_READINESS.md` with progressive compliance roadmap

---

## Phase Mapping

### Phase 1 (MVP) - Current
**Scope**: PPM + Expense + BIR
**Enterprise Alignment**: ~5% of enterprise blueprint
**Focus**: Core finance workflows, BIR compliance, OCR processing

### Phase 1.5 (SRM)
**Scope**: Supplier Rate Management
**Enterprise Alignment**: ~10% of enterprise blueprint
**Focus**: Ariba-style procurement patterns

### Phase 2 (MSFT OSS)
**Scope**: Microsoft OSS patterns + design system
**Enterprise Alignment**: ~15% of enterprise blueprint
**Focus**: Playwright, Fluent UI, TypeScript, accessibility

### Phase 3 (Enterprise)
**Scope**: Complete enterprise platform
**Enterprise Alignment**: 100% of enterprise blueprint
**Focus**: Data engineering, AI/ML, security compliance, infrastructure

---

## Reference Files Usage

### `SECURITY_CHECKLIST.md`
**Use for**:
- Progressive security hardening
- SOC 2/ISO 27001 compliance planning
- Security acceptance criteria per phase

**Example**:
```markdown
# Phase 1 Security Checklist (20 of 74 controls)
- [x] Multi-tenant RLS enforcement
- [x] API authentication (JWT)
- [x] Secrets in environment variables
- [x] HTTPS-only (TLS 1.3)
- [ ] SOC 2 audit trail (Phase 3)
- [ ] ISO 27001 certification (Phase 3)
```

### `complete-schema.sql`
**Use for**:
- Understanding advanced PostgreSQL patterns
- RLS policy examples
- Audit trigger implementations
- Vector embedding table structures

**Example**:
```sql
-- Cherry-pick audit trigger pattern from enterprise schema
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
BEGIN
  -- Implementation from complete-schema.sql
  -- Adapted for canonical schema
END;
$$ LANGUAGE plpgsql;
```

### `ARCHITECTURE.md`
**Use for**:
- Infrastructure planning (Phase 3)
- Cost-benefit analysis for enterprise replacement
- Technology stack evaluation
- Deployment architecture design

**Example**:
Reference Traefik configuration for reverse proxy setup in Phase 3.

---

## Canonical Schema Alignment

**Canonical Source of Truth**: `packages/db/sql/*.sql` in main repo

**Enterprise Schema Role**: **Reference ONLY**

**Conflict Resolution**:
1. If canonical schema conflicts with enterprise schema → canonical wins
2. If enterprise pattern improves canonical → propose change via PR
3. If enterprise feature is Phase 3+ → document in FEATURE_FLAGS.md as disabled

---

## Security Compliance Roadmap

Based on `SECURITY_CHECKLIST.md`, create progressive compliance targets:

**Phase 1 (MVP)**:
- [ ] 20 of 74 controls (27%) - Focus: Multi-tenant RLS, API auth, secrets management
- [ ] Acceptance criteria: Zero RLS violations, HTTPS-only, no hardcoded secrets

**Phase 1.5 (SRM)**:
- [ ] 30 of 74 controls (41%) - Add: Supplier data encryption, rate card approval audit

**Phase 2 (MSFT OSS)**:
- [ ] 45 of 74 controls (61%) - Add: WCAG 2.1 AA compliance, E2E test coverage

**Phase 3 (Enterprise)**:
- [ ] 74 of 74 controls (100%) - Full SOC 2 Type II + ISO 27001 certification

---

## Contact & Questions

**For Phase 1 questions**: Use canonical schema and Phase 1 docs
**For enterprise blueprint questions**: Reference this directory
**For conflicts**: Canonical schema always wins

**Repository Structure**:
```
archi-agent-framework/
├── packages/db/sql/        # Canonical schema (source of truth)
├── docs/
│   ├── ROADMAP.md          # Phase timeline
│   ├── FEATURE_FLAGS.md    # Feature gating
│   └── DATA_MODEL.md       # Canonical data model
└── ref/enterprise-blueprint/  # Enterprise reference (this directory)
    ├── security/
    ├── data-models/
    ├── docs/
    └── README.md            # This file
```

---

**Last Updated**: 2025-12-09
**Next Review**: After Phase 2 completion
**Maintainer**: Reference-only, no active maintenance required
