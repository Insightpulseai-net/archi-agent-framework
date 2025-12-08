# Product Roadmap - Finance SSC Platform

**Vision**: Replace $3.1M/year enterprise software stack with self-hosted alternatives achieving 95%+ feature parity at <$50K/year total cost.

---

## Phase 1: PPM + Expense + BIR (MVP) - **IN PROGRESS**

**Timeline**: 3-4 weeks (Current Phase)
**Scope**: Multi-agency Finance Shared Services Center with BIR compliance
**Acceptance Gates**: All gates from CLAUDE.md Section 6

### Deliverables (5 Worktrees)

✅ **Worktree 1 - Medallion Schema** (`feature/medallion-schema`)
- Bronze/Silver/Gold/Platinum data layers
- Multi-tenant RLS (tenant_id, workspace_id)
- pgvector for RAG/embeddings
- Canonical types (timestamptz, uuid, jsonb, text enums)

✅ **Worktree 2 - Expense Classifier** (`feature/expense-rag`)
- RAG-enhanced expense categorization
- Vector similarity search (cosine ≥0.75)
- Policy validation engine
- Platinum analytics insights

✅ **Worktree 3 - PPM Workflows** (`feature/ppm-workflows`)
- 8 BIR workflows (n8n JSON): 1601-C, 0619-E, 2550Q, 1702-RT, 1601-EQ, 1601-FQ, 2550M, 1600
- Task creation, deadline alerts, compliance monitoring
- 3-level approval workflow (Finance Supervisor → Senior Manager → Director)
- 4-level escalation (low/medium/high/critical)

✅ **Worktree 4 - M365 Copilot UI** (`feature/m365-ui`)
- Next.js 14 App Router + Tailwind CSS
- Microsoft Fluent UI design patterns
- 3 dashboards: Task Queue, BIR Status, OCR Confidence
- Real-time Supabase subscriptions

✅ **Worktree 5 - Integration Layer** (`feature/integration-layer`)
- 3 Supabase Edge Functions (Deno)
- 3 Next.js API routes (REST)
- 3 Playwright E2E test suites

### Current Status

**Completed**: All 5 worktrees built and committed
**Next**: Merge to main + run validation gates + deploy

### Success Criteria

- [ ] OCR backend health: P95 ≤ 30s
- [ ] OCR smoke test: confidence ≥ 0.60
- [ ] Task bus operational: no stuck tasks >5min
- [ ] DB migrations applied (schema hash match)
- [ ] RLS enforced on all public tables
- [ ] Visual parity: SSIM ≥0.97 (mobile), ≥0.98 (desktop)

---

## Phase 1.5: SRM (Supplier Rate Management) - **BLOCKED**

**Timeline**: 1-2 weeks (After Phase 1 ships)
**Scope**: Ariba-style supplier management and rate cards
**Trigger**: All Phase 1 acceptance gates pass

### Deliverables

**Schema** (Provided SQL files):
- `06_srm_suppliers.sql` - Supplier master data
- `07_srm_rate_cards.sql` - Service rate definitions
- `08_srm_rate_card_items.sql` - Line-level pricing
- `09_srm_requests.sql` - Rate inquiry workflow

**UI Routes**:
- `/srm/suppliers` - Supplier list and management
- `/srm/rate-cards` - Rate card catalog
- `/srm/requests` - Rate inquiry requests

**Integration Points**:
- SRM ↔ PPM: Link suppliers to projects
- SRM ↔ Expense: Auto-validate vendor rates

### Success Criteria

- [ ] Schema deployed to Supabase (RLS enforced)
- [ ] Supplier CRUD operations functional
- [ ] Rate card approval workflow operational
- [ ] Visual parity maintained (SSIM thresholds)

---

## Phase 2: Microsoft OSS + Design System - **BLOCKED**

**Timeline**: 2-3 weeks (After Phase 1.5 ships)
**Scope**: Microsoft OSS patterns and design system formalization
**Trigger**: Phase 1.5 acceptance gates pass

### Deliverables

**Documentation**:
- `REFERENCES_MICROSOFT_OSS.md` - Complete Microsoft OSS guide
  - Playwright (E2E testing)
  - Fluent UI (design system)
  - TypeScript (type safety)
  - Official documentation patterns

**Design System**:
- Formalize Fluent UI token system
- Component library documentation
- Accessibility compliance (WCAG 2.1 AA)
- Dark mode support

**Progressive Adoption**:
- Migrate existing UI to Fluent patterns
- Standardize component structure
- Implement design system CI checks

### Success Criteria

- [ ] All UI components use Fluent design tokens
- [ ] WCAG 2.1 AA compliance (90%+)
- [ ] Dark mode functional across all dashboards
- [ ] Design system docs published

---

## Phase 3: Enterprise Blueprint - **FUTURE**

**Timeline**: 6-12 months (After Phase 2 ships)
**Scope**: Complete enterprise platform per `ref/enterprise-blueprint/`
**Reference**: `/Users/tbwa/Downloads/insightpulse-enterprise-v2.zip`

### Architecture Overview

**Enterprise Stack Replacement**:
- SAP S/4HANA → Odoo 18 CE + ipai_*
- SAP Concur → ipai_travel_expense
- SAP Ariba → ipai_procurement
- Microsoft Dynamics 365 → Odoo 18 CE
- Microsoft Power BI → Apache Superset
- Databricks → Self-hosted Spark + MLflow
- Snowflake → ClickHouse + DuckDB

**Cost Target**: $17K/year vs $3.1M enterprise (ROI: 18,353%)

### Key Components

**Data Engineering**:
- Apache Spark 3.5 (Databricks parity)
- Apache Airflow 2.8 (orchestration)
- dbt Core (transformations)
- Great Expectations (quality)

**AI/ML Platform**:
- Ollama (LLM runtime)
- MLflow (experiment tracking)
- LangChain (RAG pipeline)
- CrewAI (multi-agent orchestration)
- Chroma + pgvector (vector DB)

**Security**:
- 74 SOC 2/ISO 27001 controls
- TLS 1.3 + WAF + OAuth2
- Secrets management (Vault)
- Audit logging (immutable)

**Reference Files**:
- `ref/enterprise-blueprint/docs/ARCHITECTURE.md` - Master architecture
- `ref/enterprise-blueprint/security/SECURITY_CHECKLIST.md` - 74 controls
- `ref/enterprise-blueprint/data-models/complete-schema.sql` - Full schema

### Success Criteria

- [ ] Replace 12+ enterprise applications
- [ ] Achieve 95%+ feature parity
- [ ] Maintain <$50K/year total cost
- [ ] SOC 2 Type II compliance
- [ ] ISO 27001 certification

---

## Feature Flags

See `docs/FEATURE_FLAGS.md` for granular feature gating by phase.

---

## Deployment Strategy

**Phase 1**: DigitalOcean App Platform + Supabase + Vercel
**Phase 1.5**: Same stack, incremental schema updates
**Phase 2**: Same stack, UI enhancements
**Phase 3**: Self-hosted Docker Swarm or Kubernetes

---

## Risk Management

**Phase 1 Risks**:
- Visual parity regression → Automated SSIM checks
- BIR compliance drift → Validation against BIR_SCHEDULE_2026.xlsx
- Multi-tenant security → RLS enforcement tests

**Phase 1.5 Risks**:
- SRM schema conflicts → Dry-run migrations before deploy
- Supplier data quality → Validation rules in schema

**Phase 3 Risks**:
- Infrastructure complexity → Phased rollout per service
- Migration costs → Parallel run existing + new systems

---

## Success Metrics

**Phase 1**:
- BIR compliance rate: ≥95%
- OCR accuracy: ≥94% average confidence
- Task processing: <5min end-to-end

**Phase 1.5**:
- Supplier onboarding: <24 hours
- Rate card approval: <48 hours

**Phase 3**:
- Total cost savings: ≥$3M/year
- Feature parity: ≥95% vs enterprise
- Uptime: ≥99.9%

---

**Last Updated**: 2025-12-09
**Current Phase**: Phase 1 (Merge + Deploy)
**Next Milestone**: Phase 1 acceptance gates
