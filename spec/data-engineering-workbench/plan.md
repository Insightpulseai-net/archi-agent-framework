# Data Engineering Workbench - Implementation Plan

## Document Control
- **Version**: 1.0.0
- **Status**: Draft
- **Last Updated**: 2025-12-08
- **Author**: InsightPulseAI Platform Team

---

## 1. Target Architecture

### 1.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INSIGHTPULSEAI ECOSYSTEM                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Figma     │    │   GitHub    │    │ Squarespace │    │  External   │  │
│  │  Dev Mode   │    │    Repos    │    │    DNS      │    │    APIs     │  │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘  │
│         │                  │                  │                  │          │
│         └──────────────────┼──────────────────┼──────────────────┘          │
│                            │                  │                             │
│  ┌─────────────────────────┼──────────────────┼─────────────────────────┐   │
│  │                    NGINX REVERSE PROXY (TLS)                         │   │
│  │         workbench.insightpulseai.net / n8n.insightpulseai.net       │   │
│  └─────────────────────────┬──────────────────┬─────────────────────────┘   │
│                            │                  │                             │
│  ┌─────────────────────────┴──────────────────┴─────────────────────────┐   │
│  │                    DATA ENGINEERING WORKBENCH                         │   │
│  │  ┌──────────────────────────────────────────────────────────────┐    │   │
│  │  │                      FRONTEND LAYER                          │    │   │
│  │  │   Next.js + React + Tailwind + Material Web                  │    │   │
│  │  │   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │    │   │
│  │  │   │Dashboard │ │ Notebook │ │ Pipeline │ │ Catalog  │       │    │   │
│  │  │   │  View    │ │  Editor  │ │ Builder  │ │ Browser  │       │    │   │
│  │  │   └──────────┘ └──────────┘ └──────────┘ └──────────┘       │    │   │
│  │  └──────────────────────────────────────────────────────────────┘    │   │
│  │                              │                                        │   │
│  │  ┌──────────────────────────────────────────────────────────────┐    │   │
│  │  │                       API LAYER                               │    │   │
│  │  │   FastAPI / Express                                           │    │   │
│  │  │   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │    │   │
│  │  │   │ Notebook │ │ Pipeline │ │ Catalog  │ │Connection│       │    │   │
│  │  │   │   API    │ │   API    │ │   API    │ │   API    │       │    │   │
│  │  │   └──────────┘ └──────────┘ └──────────┘ └──────────┘       │    │   │
│  │  └──────────────────────────────────────────────────────────────┘    │   │
│  │                              │                                        │   │
│  │  ┌──────────────────────────────────────────────────────────────┐    │   │
│  │  │                    EXECUTION LAYER                            │    │   │
│  │  │   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │    │   │
│  │  │   │ Jupyter  │ │  DuckDB  │ │ Temporal │ │  Redis   │       │    │   │
│  │  │   │  Kernel  │ │  Engine  │ │  Worker  │ │  Queue   │       │    │   │
│  │  │   └──────────┘ └──────────┘ └──────────┘ └──────────┘       │    │   │
│  │  └──────────────────────────────────────────────────────────────┘    │   │
│  │                              │                                        │   │
│  │  ┌──────────────────────────────────────────────────────────────┐    │   │
│  │  │                     STORAGE LAYER                             │    │   │
│  │  │   ┌──────────┐ ┌──────────┐ ┌──────────┐                     │    │   │
│  │  │   │PostgreSQL│ │  MinIO   │ │  File    │                     │    │   │
│  │  │   │ (Meta)   │ │ (Objects)│ │ (Local)  │                     │    │   │
│  │  │   └──────────┘ └──────────┘ └──────────┘                     │    │   │
│  │  └──────────────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      INTEGRATED SERVICES                             │   │
│  │                                                                       │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │   │
│  │  │ odoo-erp-prod│  │   superset   │  │ocr-service   │               │   │
│  │  │ 159.223.75.  │  │  -analytics  │  │  -droplet    │               │   │
│  │  │     148      │  │              │  │188.166.237.  │               │   │
│  │  │              │  │              │  │     231      │               │   │
│  │  │  ┌────────┐  │  │  ┌────────┐  │  │  ┌────────┐  │               │   │
│  │  │  │Odoo 18 │  │  │  │Superset│  │  │  │  OCR   │  │               │   │
│  │  │  │Postgres│  │  │  │Postgres│  │  │  │  LLM   │  │               │   │
│  │  │  └────────┘  │  │  └────────┘  │  │  └────────┘  │               │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │   │
│  │                                                                       │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │   │
│  │  │     n8n      │  │mcp-coordinator│ │   Agents     │               │   │
│  │  │  Automation  │  │              │  │(odoo-dev,    │               │   │
│  │  │     Bus      │  │              │  │finance-ssc,  │               │   │
│  │  │              │  │              │  │devops,bi)    │               │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA FLOW LAYERS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SOURCES                    WORKBENCH                      DESTINATIONS     │
│  ═══════                    ═════════                      ════════════     │
│                                                                             │
│  ┌─────────────┐     ┌─────────────────────────┐     ┌─────────────┐       │
│  │ Odoo CE/18  │     │      BRONZE LAYER       │     │  Superset   │       │
│  │  - GL       │────▶│  (Raw, Immutable)       │     │  Dashboards │       │
│  │  - AP/AR    │     │  - Partitioned by date  │     └──────▲──────┘       │
│  │  - Inventory│     │  - Full audit trail     │            │              │
│  └─────────────┘     └───────────┬─────────────┘            │              │
│                                  │                          │              │
│  ┌─────────────┐     ┌───────────▼─────────────┐     ┌──────┴──────┐       │
│  │ OCR Service │     │      SILVER LAYER       │     │   Agents    │       │
│  │  - Invoices │────▶│  (Cleaned, Validated)   │────▶│  - RAG Data │       │
│  │  - Receipts │     │  - Deduplicated         │     │  - Context  │       │
│  │  - Docs     │     │  - Type-enforced        │     └─────────────┘       │
│  └─────────────┘     └───────────┬─────────────┘                           │
│                                  │                                          │
│  ┌─────────────┐     ┌───────────▼─────────────┐     ┌─────────────┐       │
│  │ External    │     │       GOLD LAYER        │     │   Reports   │       │
│  │  - APIs     │────▶│  (Business-Ready)       │────▶│  - Finance  │       │
│  │  - Files    │     │  - Aggregated           │     │  - Ops      │       │
│  │  - Events   │     │  - SCD Type 2           │     └─────────────┘       │
│  └─────────────┘     └─────────────────────────┘                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Technology Stack Summary

| Component | Technology | Version | Rationale |
|-----------|------------|---------|-----------|
| **Frontend** | Next.js | 14.x | SSR, React ecosystem, TypeScript |
| **UI Components** | Material Web + Tailwind | 3.x | Consistent with Scout/AI Workbench |
| **API Server** | FastAPI | 0.104+ | High performance, OpenAPI |
| **Notebook Kernel** | Jupyter Server | 2.x | Industry standard, extensible |
| **Query Engine** | DuckDB | 0.9+ | Fast OLAP, low memory |
| **Orchestration** | Temporal.io | Latest | Durable, scalable workflows |
| **Cache/Queue** | Redis | 7.x | Fast, proven |
| **Metadata DB** | PostgreSQL | 15+ | ACID, JSON support |
| **Object Storage** | MinIO | Latest | S3-compatible, self-hosted |
| **Reverse Proxy** | nginx | 1.24+ | TLS termination, rate limiting |
| **Containers** | Docker + Compose | Latest | Reproducible deployment |

---

## 2. Component Design

### 2.1 Notebook Service Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     NOTEBOOK SERVICE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   NOTEBOOK API                           │   │
│  │   - CRUD operations for notebooks                        │   │
│  │   - Cell execution management                            │   │
│  │   - Version control integration                          │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │                                   │
│  ┌──────────────────────────▼──────────────────────────────┐   │
│  │                  KERNEL MANAGER                          │   │
│  │   - Kernel lifecycle (start, stop, restart)              │   │
│  │   - Session management                                   │   │
│  │   - Resource allocation                                  │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │                                   │
│  ┌──────────────────────────▼──────────────────────────────┐   │
│  │                    KERNELS                               │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │   │
│  │  │  SQL    │  │ Python  │  │   dbt   │  │  Shell  │    │   │
│  │  │ (DuckDB)│  │ (IPython│  │ (Core)  │  │  (Bash) │    │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Pipeline Orchestration Design

```
┌─────────────────────────────────────────────────────────────────┐
│                  PIPELINE ORCHESTRATION                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 PIPELINE DEFINITIONS                     │   │
│  │   - YAML/Python pipeline specs                           │   │
│  │   - Visual DAG representation                            │   │
│  │   - Schedule configurations                              │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │                                   │
│  ┌──────────────────────────▼──────────────────────────────┐   │
│  │                 TEMPORAL WORKFLOWS                       │   │
│  │   - Durable execution guarantees                         │   │
│  │   - Retry and timeout policies                           │   │
│  │   - Workflow versioning                                  │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │                                   │
│  ┌──────────────────────────▼──────────────────────────────┐   │
│  │                   TASK WORKERS                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │   │
│  │  │  Query   │  │Transform │  │  Export  │              │   │
│  │  │  Worker  │  │  Worker  │  │  Worker  │              │   │
│  │  └──────────┘  └──────────┘  └──────────┘              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Data Catalog Design

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA CATALOG                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  METADATA STORE                          │   │
│  │   - Table/Column definitions                             │   │
│  │   - Data types and constraints                           │   │
│  │   - Business descriptions                                │   │
│  │   - Classification tags                                  │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │                                   │
│  ┌──────────────────────────▼──────────────────────────────┐   │
│  │                  LINEAGE TRACKER                         │   │
│  │   - Source → Target mappings                             │   │
│  │   - Column-level dependencies                            │   │
│  │   - Transformation history                               │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │                                   │
│  ┌──────────────────────────▼──────────────────────────────┐   │
│  │                   SEARCH INDEX                           │   │
│  │   - Full-text search on metadata                         │   │
│  │   - Faceted filtering                                    │   │
│  │   - Usage-based ranking                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Implementation Phases

### Phase 1: Foundation (MVP)
**Duration**: 4 weeks
**Goal**: Basic working notebook environment with Odoo connectivity

```
Week 1: Infrastructure Setup
├── Provision workbench droplet (or configure on odoo-erp-prod)
├── Docker environment setup
├── PostgreSQL metadata database
├── nginx + TLS configuration
└── Basic authentication

Week 2: Core Services
├── FastAPI backend scaffold
├── Next.js frontend scaffold
├── Jupyter kernel integration
├── DuckDB query engine setup
└── Redis for sessions/queue

Week 3: Notebook MVP
├── Notebook CRUD operations
├── SQL cell execution
├── Python cell execution
├── Output rendering
└── Basic error handling

Week 4: Integration & Testing
├── Odoo PostgreSQL connection
├── Basic data queries
├── End-to-end testing
├── Documentation
└── MVP deployment
```

**Deliverables**:
- Working notebook environment
- SQL and Python execution
- Odoo database connectivity
- Basic authentication
- Deployment documentation

---

### Phase 2: Integration
**Duration**: 4 weeks
**Goal**: Full integration with existing InsightPulseAI services

```
Week 5: Odoo Integration
├── XML-RPC connector
├── REST API connector
├── Connection management UI
├── Credential storage
└── Connection testing

Week 6: Pipeline Basics
├── Pipeline definition schema
├── Simple scheduler (cron-based)
├── Job execution engine
├── Execution logging
└── Manual trigger UI

Week 7: External Integrations
├── OCR service connector
├── Superset API integration
├── n8n webhook bridge
├── Agent event hooks
└── Error handling

Week 8: Data Catalog MVP
├── Schema discovery
├── Table/column metadata
├── Basic search
├── Data preview
└── Lineage basics
```

**Deliverables**:
- Full Odoo integration (RPC + REST)
- OCR pipeline template
- Superset connectivity
- Basic pipeline scheduling
- Data catalog with search

---

### Phase 3: Advanced Features
**Duration**: 4 weeks
**Goal**: Enterprise features for scale and governance

```
Week 9: Visual Pipeline Builder
├── DAG editor UI
├── Node library (sources, transforms, destinations)
├── Drag-and-drop interface
├── Code generation from visual
└── Visual ↔ Code sync

Week 10: Real-Time & CDC
├── Debezium integration (optional)
├── Event streaming setup
├── Real-time data views
├── Delta lake patterns
└── Change notifications

Week 11: Agent Integration
├── MCP connector
├── Agent task triggers
├── Data-to-agent events
├── Agent result handling
└── RAG data preparation

Week 12: Monitoring & Alerts
├── Metrics collection
├── Dashboard (internal or Superset)
├── Alert rules engine
├── Notification channels
└── SLA tracking
```

**Deliverables**:
- Visual pipeline builder
- Real-time data capabilities
- Full agent integration
- Monitoring and alerting
- SLA dashboards

---

### Phase 4: Enterprise Polish
**Duration**: Ongoing
**Goal**: Production hardening and advanced features

```
Ongoing Improvements:
├── Performance optimization
├── Advanced security (row-level, column masking)
├── Multi-workspace support
├── Collaboration features
├── Custom extensions API
├── Advanced lineage
├── Data quality framework
└── Disaster recovery
```

---

## 4. Deployment Strategy

### 4.1 Infrastructure Decision

**Option A: Dedicated Droplet (Recommended)**
```
New droplet: workbench-prod
├── Size: 4 vCPU, 8GB RAM, 160GB SSD (minimum)
├── Region: Same as odoo-erp-prod
├── Networking: VPC with existing droplets
└── Cost: ~$48/month
```

**Pros**:
- Isolated resources
- Independent scaling
- Clear security boundary
- No impact on Odoo performance

**Cons**:
- Additional infrastructure cost
- More components to manage

**Option B: Co-locate on odoo-erp-prod**
```
Existing droplet: odoo-erp-prod (159.223.75.148)
├── Add workbench containers alongside Odoo
├── Share PostgreSQL (separate databases)
└── Share nginx (add vhost)
```

**Pros**:
- Lower cost
- Simpler networking
- Direct database access

**Cons**:
- Resource contention risk
- Blast radius concerns
- Scaling constraints

**Recommendation**: Option A for production, Option B acceptable for initial development.

### 4.2 Container Architecture

```yaml
# docker-compose.yml structure
services:
  # Core Application
  workbench-frontend:     # Next.js frontend
  workbench-api:          # FastAPI backend

  # Execution Layer
  jupyter-server:         # Notebook kernel manager
  temporal-server:        # Workflow orchestration
  temporal-worker:        # Task execution

  # Data Layer
  postgres:               # Metadata database
  redis:                  # Cache and queues
  minio:                  # Object storage
  duckdb:                 # Query engine (embedded)

  # Infrastructure
  nginx:                  # Reverse proxy (if not shared)
```

### 4.3 Networking

```
┌─────────────────────────────────────────────────────────────┐
│                    NETWORK TOPOLOGY                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Internet                                                   │
│      │                                                      │
│      ▼                                                      │
│  ┌───────────────────────────────────────────────────────┐ │
│  │         Squarespace DNS (insightpulseai.net)          │ │
│  │  workbench.insightpulseai.net → [DROPLET_IP]          │ │
│  └───────────────────────────────────────────────────────┘ │
│      │                                                      │
│      ▼                                                      │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              DigitalOcean VPC                          │ │
│  │                                                         │ │
│  │  ┌─────────────┐    ┌─────────────┐                   │ │
│  │  │ workbench   │◀──▶│ odoo-erp    │                   │ │
│  │  │   droplet   │    │   -prod     │                   │ │
│  │  │             │    │             │                   │ │
│  │  │ nginx:443   │    │ nginx:443   │                   │ │
│  │  │ api:8000    │    │ odoo:8069   │                   │ │
│  │  │ jupyter:8888│    │ pg:5432     │                   │ │
│  │  └─────────────┘    └─────────────┘                   │ │
│  │         │                                              │ │
│  │         ▼                                              │ │
│  │  ┌─────────────┐                                      │ │
│  │  │ ocr-service │                                      │ │
│  │  │   droplet   │                                      │ │
│  │  └─────────────┘                                      │ │
│  │                                                         │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Security Implementation

### 5.1 Authentication Flow

```
┌─────────┐     ┌─────────────┐     ┌──────────────┐
│  User   │────▶│  Workbench  │────▶│    Auth      │
│         │     │   Frontend  │     │   Provider   │
└─────────┘     └──────┬──────┘     │(auth.insight │
                       │            │ pulseai.net) │
                       │            └──────┬───────┘
                       │                   │
                       ▼                   ▼
               ┌─────────────┐     ┌──────────────┐
               │  Workbench  │◀────│    JWT       │
               │     API     │     │   Token      │
               └─────────────┘     └──────────────┘
```

### 5.2 Secret Management

| Secret Type | Storage | Access Method |
|-------------|---------|---------------|
| DB credentials | .env file | Environment variable |
| API keys | .env file | Environment variable |
| Encryption keys | Docker secrets | Mounted file |
| User sessions | Redis | Memory only |
| Connection passwords | Encrypted in DB | Decrypted at runtime |

### 5.3 Network Security Rules

```
# Firewall rules (ufw)
Port 22   → SSH (IP restricted)
Port 80   → HTTP (redirect to 443)
Port 443  → HTTPS (public)
Port 5432 → PostgreSQL (VPC only)
Port 6379 → Redis (localhost only)
Port 8000 → API (localhost only)
Port 8888 → Jupyter (localhost only)
```

---

## 6. Backup & Recovery Strategy

### 6.1 Backup Schedule

| Component | Frequency | Retention | Method |
|-----------|-----------|-----------|--------|
| PostgreSQL | Hourly | 24 hours | pg_dump |
| PostgreSQL | Daily | 30 days | pg_dump |
| PostgreSQL | Weekly | 90 days | pg_dump |
| MinIO objects | Daily | 30 days | mc mirror |
| Notebooks | On save | Unlimited | Git |
| Configuration | Daily | 90 days | Tar + encrypt |

### 6.2 Recovery Procedures

```
RTO: < 1 hour
├── Database restore: 30 minutes
├── Container restart: 10 minutes
├── Configuration apply: 10 minutes
└── Validation: 10 minutes

RPO: < 15 minutes
├── Hourly backups
├── WAL archiving (if enabled)
└── Real-time notebook git sync
```

---

## 7. Monitoring & Observability

### 7.1 Metrics to Collect

```yaml
# Application Metrics
workbench_notebook_executions_total:
  type: counter
  labels: [kernel_type, status]

workbench_query_duration_seconds:
  type: histogram
  labels: [query_type, data_source]

workbench_pipeline_runs_total:
  type: counter
  labels: [pipeline_name, status]

# Infrastructure Metrics
container_cpu_usage_percent
container_memory_usage_bytes
postgres_connections_active
redis_connected_clients
```

### 7.2 Alert Rules

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| HighErrorRate | >5% errors in 5m | P2 | Page on-call |
| SlowQueries | P95 >30s | P3 | Slack notification |
| DiskSpace | >80% used | P2 | Email + Slack |
| ServiceDown | No heartbeat 2m | P1 | Page + escalate |
| PipelineFailed | Critical pipeline fails | P1 | Page + escalate |

---

## 8. Success Criteria

### 8.1 Phase 1 Success Criteria
- [ ] Notebook environment accessible via HTTPS
- [ ] SQL queries execute against Odoo database
- [ ] Python code executes with pandas/numpy
- [ ] Authentication enforced on all endpoints
- [ ] Deployment documented and reproducible

### 8.2 Phase 2 Success Criteria
- [ ] Month-end finance pipeline runs successfully
- [ ] OCR → Odoo expense flow working
- [ ] Data catalog shows all connected sources
- [ ] Scheduled jobs run reliably

### 8.3 Phase 3 Success Criteria
- [ ] Visual pipeline builder functional
- [ ] Agent integration triggers working
- [ ] Real-time data updates visible
- [ ] Monitoring dashboards operational

### 8.4 Overall Success Metrics
- Month-end close: 5 days → 2 days
- Manual data tasks: Reduced 75%
- Pipeline success rate: >99%
- User adoption: >70% of target users

---

## Appendix A: DNS Configuration

Add to Squarespace DNS:
```
workbench.insightpulseai.net  A     [DROPLET_IP]
*.workbench.insightpulseai.net  A   [DROPLET_IP] (optional)
```

## Appendix B: Resource Estimates

| Resource | Phase 1 | Phase 2 | Phase 3 |
|----------|---------|---------|---------|
| CPU | 2 vCPU | 4 vCPU | 4-8 vCPU |
| Memory | 4 GB | 8 GB | 8-16 GB |
| Storage | 80 GB | 160 GB | 320 GB |
| Cost/month | ~$24 | ~$48 | ~$96 |
