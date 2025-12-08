# Data Engineering Workbench - Product Requirements Document

## Document Control
- **Version**: 1.0.0
- **Status**: Draft
- **Last Updated**: 2025-12-08
- **Author**: InsightPulseAI Platform Team

---

## 0. Executive Summary

The **Data Engineering Workbench** is a Databricks-style, self-hosted platform that serves as the central hub for building, testing, and deploying data pipelines within the InsightPulseAI ecosystem. It sits at the heart of the development pipeline—after design (Figma) and planning (Spec Kit), and before production deployment.

### Key Value Propositions
1. **Unified Development Environment**: One place for SQL, Python, and visual pipeline building
2. **Full Stack Integration**: Native connections to Odoo, Superset, OCR, and AI agents
3. **Enterprise Governance**: Audit trails, access control, and compliance built-in
4. **Self-Hosted Control**: No SaaS lock-in, all data stays in fin-workspace

---

## 1. Problem Statement

### Current Pain Points
1. **Fragmented Tooling**: Data engineering tasks scattered across n8n, scripts, and manual processes
2. **No Central Visibility**: Hard to track what pipelines exist, their status, and dependencies
3. **Limited Collaboration**: Engineers can't easily share and review transformation logic
4. **Audit Gaps**: Finance-critical flows lack comprehensive audit trails
5. **Slow Iteration**: No sandbox environment for safe experimentation

### Business Impact
- Delayed month-end close due to manual data reconciliation
- Risk of data quality issues reaching production
- Difficulty onboarding new team members
- Compliance concerns for financial data handling

---

## 2. User Personas

### 2.1 Finance SSC Lead (Primary)
**Name**: Maria - Finance Shared Services Center Lead
**Goals**:
- Ensure accurate, timely financial reporting
- Maintain audit trail for all financial data transformations
- Self-serve on common data requests without engineering dependency

**Pain Points**:
- Waiting for engineers to build simple reports
- No visibility into when data was last refreshed
- Manual Excel reconciliation processes

**Success Metrics**:
- < 2 day month-end close (from 5 days)
- 100% audit coverage for financial transformations
- Self-service for 80% of routine reports

---

### 2.2 DevOps Engineer
**Name**: Jake - Platform & Infrastructure Engineer
**Goals**:
- Maintain stable, observable data infrastructure
- Quick deployment of new pipelines
- Minimal operational overhead

**Pain Points**:
- Ad-hoc scripts with no monitoring
- Debugging failed jobs without proper logs
- Manual scaling during peak loads

**Success Metrics**:
- 99.5% job success rate
- < 15 min mean time to detect failures
- Automated scaling based on load

---

### 2.3 Data Engineer
**Name**: Chen - Senior Data Engineer
**Goals**:
- Build robust, tested data pipelines
- Easy integration with existing data sources
- Version control and collaboration on transformations

**Pain Points**:
- No proper development environment
- Can't easily test changes before production
- Manual dependency management

**Success Metrics**:
- < 1 hour to deploy new pipeline to staging
- 80% test coverage on all transformations
- Zero production incidents from untested code

---

### 2.4 Agent Orchestrator
**Name**: Alex - AI/ML Platform Engineer
**Goals**:
- Prepare data for AI agent consumption
- Trigger agent workflows based on data events
- Monitor agent-data interactions

**Pain Points**:
- Data format mismatches with agent expectations
- No event-driven triggers for agents
- Limited observability on agent data usage

**Success Metrics**:
- < 100ms data API latency for agents
- Real-time event triggers working
- Full lineage from data to agent action

---

## 3. Core Use Cases

### UC-001: Month-End Finance Pipeline
**Priority**: P0 (Critical)
**Persona**: Finance SSC Lead, Data Engineer

**Flow**:
```
┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│ Odoo CE/18   │────▶│  Workbench    │────▶│  Superset    │
│ (Source)     │     │  (Transform)  │     │  (Report)    │
└──────────────┘     └───────────────┘     └──────────────┘
       │                    │                     │
       ▼                    ▼                     ▼
   Raw Extract         Validated &           Dashboard +
   (Bronze)          Aggregated (Gold)      Email Alert
```

**Requirements**:
- Scheduled trigger on 1st business day of month
- Extract GL transactions, AP/AR, and bank reconciliation
- Validate data completeness and integrity
- Generate standard financial reports
- Push to Superset for visualization
- Email summary to finance team
- Complete audit log of all steps

**Acceptance Criteria**:
- [ ] Pipeline completes within 2 hours
- [ ] Zero manual intervention for standard close
- [ ] All transformations logged with row counts
- [ ] Rollback capability if issues detected

---

### UC-002: OCR to Odoo Expense Pipeline
**Priority**: P0 (Critical)
**Persona**: Finance SSC Lead, Data Engineer

**Flow**:
```
┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│ Document     │────▶│  OCR Service  │────▶│  Workbench   │
│ (Image/PDF)  │     │  (Extract)    │     │  (Validate)  │
└──────────────┘     └───────────────┘     └──────────────┘
                                                  │
                           ┌──────────────────────┘
                           ▼
                    ┌──────────────┐     ┌──────────────┐
                    │  Odoo CE/18  │◀────│  Review UI   │
                    │  (Create)    │     │  (Approve)   │
                    └──────────────┘     └──────────────┘
```

**Requirements**:
- Webhook trigger from document upload
- Call OCR service for text extraction
- Parse and map to expense/vendor bill schema
- Validation rules for required fields
- Human review queue for low-confidence extractions
- Create Odoo record on approval
- Audit trail of document → record mapping

**Acceptance Criteria**:
- [ ] 90% auto-extraction accuracy for standard formats
- [ ] < 5 second processing time per document
- [ ] Human review UI for exceptions
- [ ] Full lineage from document to Odoo record

---

### UC-003: Agent Data Preparation
**Priority**: P1 (High)
**Persona**: Agent Orchestrator

**Flow**:
```
┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│ Data Sources │────▶│  Workbench    │────▶│  Agent API   │
│ (Various)    │     │  (Curate)     │     │  (Serve)     │
└──────────────┘     └───────────────┘     └──────────────┘
       │                    │                     │
       ▼                    ▼                     ▼
   Raw Data            Vector-Ready           MCP/Agent
   (Bronze)           Embeddings (Gold)       Consumption
```

**Requirements**:
- Curate data for specific agent use cases
- Generate embeddings for RAG workflows
- Serve via low-latency API
- Event triggers for data updates
- Usage tracking per agent

**Acceptance Criteria**:
- [ ] < 100ms API response time
- [ ] Automatic refresh on source data change
- [ ] Per-agent usage metrics
- [ ] Schema versioning for agent contracts

---

### UC-004: Real-Time Data Sync
**Priority**: P1 (High)
**Persona**: Data Engineer, DevOps Engineer

**Flow**:
```
┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│ Source       │────▶│  CDC/Stream   │────▶│  Workbench   │
│ (Odoo/etc)   │     │  (Debezium)   │     │  (Process)   │
└──────────────┘     └───────────────┘     └──────────────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │ Destinations │
                                          │ (Multiple)   │
                                          └──────────────┘
```

**Requirements**:
- Change data capture from Odoo PostgreSQL
- < 1 minute latency for critical tables
- Automatic schema evolution handling
- Dead letter queue for failed events
- Replay capability for recovery

**Acceptance Criteria**:
- [ ] < 60 second end-to-end latency
- [ ] Zero data loss guarantee
- [ ] Automatic retry with exponential backoff
- [ ] Schema change alerts

---

### UC-005: Data Quality Monitoring
**Priority**: P1 (High)
**Persona**: Data Engineer, Finance SSC Lead

**Requirements**:
- Automated data quality checks on all Gold tables
- Anomaly detection for volume and value changes
- Alert routing based on severity and domain
- Quality score dashboard
- Trend analysis for recurring issues

**Acceptance Criteria**:
- [ ] 100% coverage of finance-critical tables
- [ ] Alert within 5 minutes of anomaly
- [ ] Historical quality score tracking
- [ ] Root cause suggestions

---

### UC-006: Figma to Data Model Sync
**Priority**: P2 (Medium)
**Persona**: Data Engineer, Agent Orchestrator

**Flow**:
```
┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│ Figma Dev    │────▶│  Workbench    │────▶│  Schema      │
│ Mode         │     │  (Parse)      │     │  Registry    │
└──────────────┘     └───────────────┘     └──────────────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │ Code Gen     │
                                          │ (Types/API)  │
                                          └──────────────┘
```

**Requirements**:
- Extract data model hints from Figma designs
- Map to database schema definitions
- Generate TypeScript types and API contracts
- Track design ↔ data drift

**Acceptance Criteria**:
- [ ] Automatic schema suggestions from designs
- [ ] Drift detection alerts
- [ ] Generated types match design intent

---

## 4. Functional Requirements

### 4.1 Notebook Environment

| ID | Requirement | Priority |
|----|-------------|----------|
| NB-001 | Support SQL cells with syntax highlighting | P0 |
| NB-002 | Support Python cells with package management | P0 |
| NB-003 | Support dbt model cells | P1 |
| NB-004 | Real-time collaboration (multiple users) | P2 |
| NB-005 | Version history with diff view | P0 |
| NB-006 | Cell-level execution with dependency tracking | P0 |
| NB-007 | Rich output rendering (tables, charts, markdown) | P0 |
| NB-008 | Parameterized notebooks for reuse | P1 |
| NB-009 | Notebook templates library | P2 |

### 4.2 Pipeline Builder

| ID | Requirement | Priority |
|----|-------------|----------|
| PB-001 | Visual DAG editor for pipeline design | P1 |
| PB-002 | Code-first pipeline definition (YAML/Python) | P0 |
| PB-003 | Schedule management with cron syntax | P0 |
| PB-004 | Manual trigger with parameter override | P0 |
| PB-005 | Dependency management between jobs | P0 |
| PB-006 | Retry policies and failure handling | P0 |
| PB-007 | Parallel execution support | P1 |
| PB-008 | Pipeline templates for common patterns | P2 |

### 4.3 Data Catalog

| ID | Requirement | Priority |
|----|-------------|----------|
| DC-001 | Automatic schema discovery | P0 |
| DC-002 | Column-level lineage tracking | P1 |
| DC-003 | Business glossary integration | P2 |
| DC-004 | Data classification tagging | P1 |
| DC-005 | Usage statistics per table/column | P2 |
| DC-006 | Search across all metadata | P0 |
| DC-007 | Data preview with sampling | P0 |

### 4.4 Connection Management

| ID | Requirement | Priority |
|----|-------------|----------|
| CM-001 | PostgreSQL connections (Odoo, internal) | P0 |
| CM-002 | REST API connections (Superset, OCR, agents) | P0 |
| CM-003 | SFTP/S3-compatible storage | P1 |
| CM-004 | Connection testing and validation | P0 |
| CM-005 | Credential rotation support | P1 |
| CM-006 | Connection pooling and timeout config | P1 |

### 4.5 Execution Engine

| ID | Requirement | Priority |
|----|-------------|----------|
| EX-001 | Sandboxed execution environment | P0 |
| EX-002 | Resource limits per job (CPU, memory) | P0 |
| EX-003 | Execution logs with structured output | P0 |
| EX-004 | Real-time progress streaming | P1 |
| EX-005 | Kill/cancel running jobs | P0 |
| EX-006 | Job queuing with priority support | P1 |

---

## 5. Non-Functional Requirements

### 5.1 Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Notebook cell execution start | < 2 seconds | P95 latency |
| Query execution (10M rows) | < 30 seconds | P95 latency |
| Pipeline status refresh | < 1 second | P95 latency |
| API response time | < 200ms | P95 latency |
| Concurrent notebook sessions | 20+ | Simultaneous users |

### 5.2 Availability

| Metric | Target |
|--------|--------|
| Uptime | 99.5% (excluding planned maintenance) |
| Planned maintenance window | Sunday 02:00-06:00 UTC |
| RTO (Recovery Time Objective) | < 1 hour |
| RPO (Recovery Point Objective) | < 15 minutes |

### 5.3 Scalability

| Dimension | Initial | Scale Target |
|-----------|---------|--------------|
| Users | 10 | 50 |
| Notebooks | 100 | 1000 |
| Daily job runs | 200 | 2000 |
| Data volume | 100GB | 1TB |

### 5.4 Security

| Requirement | Implementation |
|-------------|----------------|
| Authentication | SSO via auth.insightpulseai.net |
| Authorization | RBAC with 4 role levels |
| Encryption at rest | AES-256 |
| Encryption in transit | TLS 1.3 |
| Audit logging | All data access + modifications |
| Secret management | HashiCorp Vault or DO secrets |

---

## 6. Integration Specifications

### 6.1 Odoo CE/OCA 18 Integration

**Connection Type**: XML-RPC + REST API
**Endpoint**: `erp.insightpulseai.net`

**Capabilities**:
- Read: All models with appropriate access rights
- Write: Controlled via workflow approval
- Bulk operations: Paginated with rate limiting

**Data Contracts**:
```yaml
# Example: GL Transaction Extract
source: odoo.account_move_line
fields:
  - id
  - move_id
  - account_id
  - partner_id
  - debit
  - credit
  - date
  - ref
  - name
filters:
  - date >= {{ start_date }}
  - date <= {{ end_date }}
  - parent_state = 'posted'
```

### 6.2 Superset Integration

**Connection Type**: REST API + PostgreSQL (shared metadata)
**Endpoint**: `superset.insightpulseai.net`

**Capabilities**:
- Trigger dataset refresh
- Create/update datasets from workbench
- Embed dashboards in workbench UI
- Share query results to Superset

### 6.3 OCR Service Integration

**Connection Type**: REST API
**Endpoint**: `ocr.insightpulseai.net` (internal: 188.166.237.231)

**Capabilities**:
- Document upload and OCR extraction
- Confidence scoring
- Structured data output

**API Contract**:
```yaml
POST /api/v1/extract
Request:
  file: binary (image/pdf)
  options:
    language: "en"
    output_format: "json"
Response:
  confidence: 0.95
  extracted:
    vendor: "ACME Corp"
    amount: 1500.00
    date: "2025-01-15"
    line_items: [...]
```

### 6.4 Agent/MCP Integration

**Connection Type**: Webhooks + REST API
**Endpoints**: Various via `mcp.insightpulseai.net`

**Agents**:
- `odoo-developer-agent`: Odoo customization tasks
- `finance-ssc-expert`: Financial analysis queries
- `devops-engineer`: Infrastructure automation
- `bi-architect`: Dashboard and report design

**Event Triggers**:
```yaml
events:
  - name: data_ready
    trigger: pipeline_complete
    payload:
      dataset: "{{ dataset_name }}"
      row_count: "{{ row_count }}"
      schema_version: "{{ schema_version }}"
```

---

## 7. UI/UX Requirements

### 7.1 Design System
- Follow Material Web components (consistent with Scout)
- Figma Dev Mode as design source of truth
- Dark mode support required
- Responsive down to 1024px width

### 7.2 Key Screens

| Screen | Purpose | Priority |
|--------|---------|----------|
| Dashboard | Overview of jobs, alerts, recent activity | P0 |
| Notebook Editor | Create and run notebooks | P0 |
| Pipeline Builder | Visual + code pipeline design | P1 |
| Data Catalog | Browse and search data assets | P0 |
| Job Monitor | View running and historical jobs | P0 |
| Connections | Manage data source connections | P0 |
| Settings | User and workspace configuration | P1 |

### 7.3 Figma References
All UI designs maintained in Figma project:
- File Key: `{{ FIGMA_FILE_KEY }}`
- Dev Mode Section: `data-engineering-workbench`

---

## 8. Success Metrics & SLAs

### 8.1 Business Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Month-end close time | 5 days | 2 days | Calendar days |
| Manual data tasks | 40/month | 10/month | Task count |
| Data quality incidents | 8/month | 2/month | Incident count |
| Self-service report requests | 20% | 80% | % of total requests |

### 8.2 Technical SLAs

| Metric | SLA | Penalty |
|--------|-----|---------|
| Pipeline success rate | 99% | P2 escalation |
| Critical job latency | ±10% of expected | Alert |
| Data freshness | Per dataset SLA | Alert → Escalation |
| Platform availability | 99.5% | P1 escalation |

### 8.3 User Satisfaction

| Metric | Target | Measurement |
|--------|--------|-------------|
| User satisfaction score | > 4.0/5.0 | Quarterly survey |
| Feature adoption rate | > 70% | Active users / total |
| Support ticket volume | < 20/month | Ticket count |

---

## 9. Release Plan

### Phase 1: Foundation (MVP)
**Target**: 4 weeks

**Scope**:
- Basic notebook environment (SQL + Python)
- Connection to Odoo PostgreSQL
- Simple job scheduling
- User authentication

### Phase 2: Integration
**Target**: 4 weeks post-MVP

**Scope**:
- Full Odoo API integration
- OCR pipeline template
- Superset integration
- Basic data catalog

### Phase 3: Advanced Features
**Target**: 4 weeks post-Phase 2

**Scope**:
- Visual pipeline builder
- Real-time data sync
- Agent integration
- Advanced monitoring

### Phase 4: Enterprise
**Target**: Ongoing

**Scope**:
- Multi-tenant support
- Advanced security features
- Performance optimization
- Extended integrations

---

## 10. Open Questions & Risks

### Open Questions
1. Should we support Jupyter notebooks natively or build custom notebook UI?
2. What's the priority for real-time collaboration vs. async review?
3. Should agent integration be event-driven or polling-based?

### Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Resource constraints on single droplet | Medium | High | Plan horizontal scaling from start |
| Odoo API rate limits | Low | Medium | Implement caching layer |
| User adoption challenges | Medium | Medium | Early user testing, training program |
| Security vulnerabilities | Low | High | Security review, penetration testing |

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| CDC | Change Data Capture |
| DAG | Directed Acyclic Graph |
| dbt | Data Build Tool |
| DuckDB | Embedded OLAP database |
| ETL | Extract, Transform, Load |
| MCP | Multi-agent Coordination Protocol |
| RAG | Retrieval-Augmented Generation |
| SCD | Slowly Changing Dimension |
| SSC | Shared Services Center |

## Appendix B: Related Documents

- [Constitution](./constitution.md)
- [Implementation Plan](./plan.md)
- [Task Breakdown](./tasks.md)
- [Architecture Documentation](../../docs/ARCHITECTURE.md)
