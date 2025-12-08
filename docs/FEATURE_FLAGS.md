# Feature Flags - Finance SSC Platform

**Purpose**: Granular feature gating to maintain focus on MVP while preserving enterprise vision.

---

## Flag Categories

- **MVP**: Phase 1 core features (always enabled)
- **SRM**: Phase 1.5 Supplier Rate Management (disabled until Phase 1 ships)
- **MSFT**: Phase 2 Microsoft OSS patterns (disabled until Phase 1.5 ships)
- **ENTERPRISE**: Phase 3 enterprise blueprint features (disabled until Phase 2 ships)

---

## Phase 1: PPM + Expense + BIR (MVP)

**Status**: ✅ All flags enabled

### Core Features

| Flag | Description | Status | Worktree |
|------|-------------|--------|----------|
| `MEDALLION_SCHEMA` | Bronze/Silver/Gold/Platinum layers | ✅ Enabled | Worktree 1 |
| `MULTI_TENANT_RLS` | Row-Level Security with tenant_id/workspace_id | ✅ Enabled | Worktree 1 |
| `PGVECTOR_RAG` | Vector embeddings for RAG | ✅ Enabled | Worktree 1 |
| `EXPENSE_CLASSIFIER` | RAG-enhanced expense categorization | ✅ Enabled | Worktree 2 |
| `EXPENSE_POLICY_ENGINE` | Policy validation rules | ✅ Enabled | Worktree 2 |
| `BIR_WORKFLOWS` | 8 BIR form workflows (n8n) | ✅ Enabled | Worktree 3 |
| `BIR_APPROVAL_3LEVEL` | 3-level approval workflow | ✅ Enabled | Worktree 3 |
| `BIR_ESCALATION_4LEVEL` | 4-level escalation (low/medium/high/critical) | ✅ Enabled | Worktree 3 |
| `M365_FLUENT_UI` | Microsoft Fluent UI design patterns | ✅ Enabled | Worktree 4 |
| `TASK_QUEUE_DASHBOARD` | Real-time task queue monitoring | ✅ Enabled | Worktree 4 |
| `BIR_STATUS_DASHBOARD` | Multi-agency BIR compliance tracking | ✅ Enabled | Worktree 4 |
| `OCR_CONFIDENCE_DASHBOARD` | PaddleOCR-VL accuracy metrics | ✅ Enabled | Worktree 4 |
| `EDGE_FUNCTIONS` | Supabase Edge Functions (task/BIR/OCR) | ✅ Enabled | Worktree 5 |
| `API_ROUTES_REST` | Next.js API routes (tasks/bir/ocr) | ✅ Enabled | Worktree 5 |
| `E2E_TESTS_PLAYWRIGHT` | End-to-end integration tests | ✅ Enabled | Worktree 5 |

### BIR Form Types

| Flag | Form Code | Description | Status |
|------|-----------|-------------|--------|
| `BIR_1601_C` | 1601-C | Monthly Remittance (Compensation) | ✅ Enabled |
| `BIR_0619_E` | 0619-E | Monthly Remittance (Expanded) | ✅ Enabled |
| `BIR_2550Q` | 2550Q | Quarterly Income Tax | ✅ Enabled |
| `BIR_1702_RT` | 1702-RT | Annual Reconciliation | ✅ Enabled |
| `BIR_1601_EQ` | 1601-EQ | Quarterly Remittance (Expanded) | ✅ Enabled |
| `BIR_1601_FQ` | 1601-FQ | Quarterly Remittance (Final) | ✅ Enabled |
| `BIR_2550M` | 2550M | Monthly Income Tax | ✅ Enabled |
| `BIR_1600` | 1600 | Monthly Withholding Tax | ✅ Enabled |

### OCR Processing

| Flag | Description | Status |
|------|-------------|--------|
| `OCR_PADDLEOCR_VL` | PaddleOCR-VL-900M model | ✅ Enabled |
| `OCR_LLM_POSTPROCESS` | OpenAI GPT-4o-mini post-processing | ✅ Enabled |
| `OCR_CONFIDENCE_THRESHOLD` | Minimum confidence: 0.60 | ✅ Enabled |
| `OCR_FIELD_EXTRACTION` | vendor_name, amount, date, category, tax_amount | ✅ Enabled |

---

## Phase 1.5: SRM (Supplier Rate Management)

**Status**: 🚫 All flags disabled (blocked until Phase 1 ships)

### Schema

| Flag | Description | Status | SQL File |
|------|-------------|--------|----------|
| `SRM_SUPPLIERS` | Supplier master data table | 🚫 Disabled | 06_srm_suppliers.sql |
| `SRM_RATE_CARDS` | Service rate definitions table | 🚫 Disabled | 07_srm_rate_cards.sql |
| `SRM_RATE_CARD_ITEMS` | Line-level pricing table | 🚫 Disabled | 08_srm_rate_card_items.sql |
| `SRM_REQUESTS` | Rate inquiry workflow table | 🚫 Disabled | 09_srm_requests.sql |

### UI Routes

| Flag | Route | Description | Status |
|------|-------|-------------|--------|
| `SRM_SUPPLIER_LIST` | `/srm/suppliers` | Supplier list and management | 🚫 Disabled |
| `SRM_RATE_CARD_CATALOG` | `/srm/rate-cards` | Rate card catalog | 🚫 Disabled |
| `SRM_REQUEST_QUEUE` | `/srm/requests` | Rate inquiry requests | 🚫 Disabled |

### Integration

| Flag | Description | Status |
|------|-------------|--------|
| `SRM_PPM_INTEGRATION` | Link suppliers to projects | 🚫 Disabled |
| `SRM_EXPENSE_INTEGRATION` | Auto-validate vendor rates | 🚫 Disabled |
| `SRM_APPROVAL_WORKFLOW` | Multi-level rate card approval | 🚫 Disabled |

---

## Phase 2: Microsoft OSS + Design System

**Status**: 🚫 All flags disabled (blocked until Phase 1.5 ships)

### Documentation

| Flag | Description | Status |
|------|-------------|--------|
| `MSFT_OSS_DOCS` | REFERENCES_MICROSOFT_OSS.md | 🚫 Disabled |
| `PLAYWRIGHT_PATTERNS` | E2E testing best practices | 🚫 Disabled |
| `FLUENT_UI_PATTERNS` | Design system guidelines | 🚫 Disabled |
| `TYPESCRIPT_PATTERNS` | Type safety conventions | 🚫 Disabled |

### Design System

| Flag | Description | Status |
|------|-------------|--------|
| `FLUENT_TOKEN_SYSTEM` | Formalized design token system | 🚫 Disabled |
| `COMPONENT_LIBRARY` | Reusable component documentation | 🚫 Disabled |
| `WCAG_COMPLIANCE` | WCAG 2.1 AA accessibility | 🚫 Disabled |
| `DARK_MODE` | Dark mode support | 🚫 Disabled |

### UI Enhancements

| Flag | Description | Status |
|------|-------------|--------|
| `FLUENT_MIGRATION` | Migrate existing UI to Fluent patterns | 🚫 Disabled |
| `COMPONENT_STANDARDIZATION` | Standardize component structure | 🚫 Disabled |
| `DESIGN_SYSTEM_CI` | Design system CI checks | 🚫 Disabled |

---

## Phase 3: Enterprise Blueprint

**Status**: 🚫 All flags disabled (blocked until Phase 2 ships)

### Data Engineering

| Flag | Component | Description | Status |
|------|-----------|-------------|--------|
| `SPARK_DATABRICKS` | Apache Spark 3.5 | Databricks parity | 🚫 Disabled |
| `AIRFLOW_ORCHESTRATION` | Apache Airflow 2.8 | ETL/ELT orchestration | 🚫 Disabled |
| `DBT_TRANSFORMATIONS` | dbt Core | Data transformations | 🚫 Disabled |
| `GREAT_EXPECTATIONS` | Great Expectations | Data quality | 🚫 Disabled |
| `KAFKA_STREAMING` | Apache Kafka | Real-time streaming | 🚫 Disabled |
| `DEBEZIUM_CDC` | Debezium | Change Data Capture | 🚫 Disabled |
| `FEAST_FEATURE_STORE` | Feast | Feature store | 🚫 Disabled |

### AI/ML Platform

| Flag | Component | Description | Status |
|------|-----------|-------------|--------|
| `OLLAMA_LLM` | Ollama | LLM runtime (llama3.2) | 🚫 Disabled |
| `MLFLOW_TRACKING` | MLflow | Experiment tracking | 🚫 Disabled |
| `LANGCHAIN_RAG` | LangChain | RAG pipeline | 🚫 Disabled |
| `CREWAI_MULTIAGENT` | CrewAI | Multi-agent orchestration | 🚫 Disabled |
| `CHROMA_VECTORDB` | Chroma | Vector database | 🚫 Disabled |
| `LABEL_STUDIO` | Label Studio | Data annotation | 🚫 Disabled |
| `HAYSTACK_SEARCH` | Haystack | Search + QA | 🚫 Disabled |
| `AUTOGLUON_AUTOML` | AutoGluon | AutoML | 🚫 Disabled |

### Security

| Flag | Component | Description | Status |
|------|-----------|-------------|--------|
| `SOC2_CONTROLS` | SOC 2 Type II | 74 security controls | 🚫 Disabled |
| `ISO27001_COMPLIANCE` | ISO 27001 | Information security | 🚫 Disabled |
| `TLS_13_WAF` | TLS 1.3 + WAF | Transport security | 🚫 Disabled |
| `OAUTH2_PROXY` | OAuth2 Proxy | Authentication gateway | 🚫 Disabled |
| `VAULT_SECRETS` | HashiCorp Vault | Secrets management | 🚫 Disabled |
| `AUDIT_LOGGING` | Immutable Audit Log | Compliance logging | 🚫 Disabled |

### Enterprise Applications

| Flag | Application | Replaces | Status |
|------|-------------|----------|--------|
| `IPAI_TRAVEL_EXPENSE` | ipai_travel_expense | SAP Concur | 🚫 Disabled |
| `IPAI_PROCUREMENT` | ipai_procurement | SAP Ariba | 🚫 Disabled |
| `IPAI_HIRE_TO_RETIRE` | ipai_hire_to_retire | SAP SuccessFactors | 🚫 Disabled |
| `IPAI_BPMN` | n8n + BPMN 2.0 | SAP Signavio | 🚫 Disabled |
| `IPAI_CRM` | Odoo CRM + ipai_crm | Salesforce | 🚫 Disabled |
| `SUPERSET_BI` | Apache Superset | Microsoft Power BI | 🚫 Disabled |
| `CLICKHOUSE_DWH` | ClickHouse + DuckDB | Snowflake | 🚫 Disabled |

---

## Flag Implementation

### Environment Variables

```bash
# Phase 1 (MVP) - All enabled
export MEDALLION_SCHEMA=true
export MULTI_TENANT_RLS=true
export PGVECTOR_RAG=true
export EXPENSE_CLASSIFIER=true
export BIR_WORKFLOWS=true
export M365_FLUENT_UI=true
export EDGE_FUNCTIONS=true

# Phase 1.5 (SRM) - All disabled until Phase 1 ships
export SRM_SUPPLIERS=false
export SRM_RATE_CARDS=false
export SRM_SUPPLIER_LIST=false

# Phase 2 (MSFT) - All disabled until Phase 1.5 ships
export MSFT_OSS_DOCS=false
export FLUENT_TOKEN_SYSTEM=false
export DARK_MODE=false

# Phase 3 (Enterprise) - All disabled until Phase 2 ships
export SPARK_DATABRICKS=false
export AIRFLOW_ORCHESTRATION=false
export OLLAMA_LLM=false
export SOC2_CONTROLS=false
```

### Runtime Checks

```typescript
// Example: Check if SRM is enabled
const isSrmEnabled = process.env.SRM_SUPPLIERS === 'true'

if (isSrmEnabled) {
  // Load SRM routes
  router.get('/srm/suppliers', getSuppliersHandler)
} else {
  // Return 404 or redirect to MVP features
  router.get('/srm/*', notFoundHandler)
}
```

### CI/CD Gates

```yaml
# .github/workflows/deploy.yml
- name: Validate Feature Flags
  run: |
    # Phase 1: All MVP flags must be enabled
    if [ "$MEDALLION_SCHEMA" != "true" ]; then
      echo "ERROR: MEDALLION_SCHEMA must be enabled"
      exit 1
    fi

    # Phase 1.5: SRM flags must be disabled until Phase 1 ships
    if [ "$SRM_SUPPLIERS" = "true" ] && [ "$PHASE_1_SHIPPED" != "true" ]; then
      echo "ERROR: SRM flags cannot be enabled until Phase 1 ships"
      exit 1
    fi
```

---

## Flag Activation Schedule

**Phase 1 Complete → Enable Phase 1.5 Flags**:
- Set `PHASE_1_SHIPPED=true` in environment
- Enable `SRM_*` flags
- Deploy schema updates

**Phase 1.5 Complete → Enable Phase 2 Flags**:
- Set `PHASE_1_5_SHIPPED=true` in environment
- Enable `MSFT_*` flags
- Deploy documentation and UI enhancements

**Phase 2 Complete → Enable Phase 3 Flags**:
- Set `PHASE_2_SHIPPED=true` in environment
- Enable `ENTERPRISE_*` flags progressively
- Deploy infrastructure changes incrementally

---

**Last Updated**: 2025-12-09
**Current Phase**: Phase 1 (MVP)
**Active Flags**: 15 MVP flags enabled, 50+ enterprise flags disabled
