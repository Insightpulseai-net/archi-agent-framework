# Data Layer - Scout Retail Medallion Architecture

Production-ready data transformation layer implementing Bronze → Silver → Gold → Platinum architecture for Scout Retail domain.

## Overview

This data layer provides the foundation for the InsightPulseAI Multi-Agent AI Workbench, implementing a complete ETL pipeline with data quality validation, lineage tracking, and AI-ready features.

### Architecture

```
External Sources (Google Drive, CSV, Webhooks)
    ↓
Bronze Layer (Raw JSONB ingestion)
    ↓ dbt run --models bronze
Silver Layer (Validated, schema-enforced)
    ↓ dbt run --models silver
Gold Layer (Business marts, aggregated)
    ↓ dbt run --models gold
Platinum Layer (AI features, embeddings)
    ↓
AI Workbench (Genie, Agents, Dashboards)
```

## Directory Structure

```
data-layer/
├── dbt-workbench/              # dbt transformation project
│   ├── models/
│   │   ├── bronze/             # Raw ingestion models
│   │   ├── silver/             # Validated models
│   │   ├── gold/               # Business marts
│   │   └── platinum/           # AI-ready views
│   ├── tests/                  # dbt test cases
│   ├── macros/                 # SQL macros
│   └── README.md
│
├── airflow/                    # Orchestration DAGs
│   ├── dags/
│   │   ├── scout_ingestion_dag.py          # Daily batch ingestion
│   │   ├── scout_transformation_dag.py     # Hourly transformations
│   │   ├── data_quality_dag.py             # Daily DQ validation
│   │   └── backfill_dag.py                 # Historical backfill
│   └── README.md
│
├── n8n-etl/                    # Real-time workflows
│   ├── workflows/
│   │   ├── real-time-transactions.json     # Webhook ingestion
│   │   ├── odoo-sync.json                  # Odoo integration
│   │   └── quality-alerts.json             # DQ alerting
│   └── README.md
│
├── schemas/                    # Schema documentation
│   ├── bronze_schema.md
│   ├── silver_schema.md
│   ├── gold_schema.md
│   ├── platinum_schema.md
│   ├── entity_relationships.md
│   └── README.md
│
└── quality/                    # Data quality framework
    ├── tests/
    │   ├── row_count_checks.sql
    │   ├── null_checks.sql
    │   ├── unique_checks.sql
    │   └── referential_integrity.sql
    ├── great_expectations/     # GE suite (future)
    └── README.md
```

## Quick Start

### Prerequisites

- PostgreSQL 15+ (Supabase)
- Python 3.11+
- dbt-postgres
- Apache Airflow 2.8+
- n8n (self-hosted or cloud)

### Setup

```bash
# 1. Clone repository
cd /Users/tbwa/archi-agent-framework/worktree/data-layer

# 2. Install dbt
pip install dbt-postgres dbt-utils

# 3. Configure profiles
cp dbt-workbench/profiles.yml.example ~/.dbt/profiles.yml
nano ~/.dbt/profiles.yml

# 4. Set environment variables
export SUPABASE_HOST=aws-1-us-east-1.pooler.supabase.com
export SUPABASE_PORT=6543
export POSTGRES_USER=postgres.xkxyvboeubffxxbebsll
export POSTGRES_PASSWORD=your_password
export POSTGRES_DB=postgres

# 5. Test connection
cd dbt-workbench
dbt debug

# 6. Install dependencies
dbt deps

# 7. Run first transformation
dbt run --models bronze
```

### First Run

```bash
# Run full pipeline
dbt run

# Run tests
dbt test

# Generate documentation
dbt docs generate
dbt docs serve
```

## Data Models

### Bronze Layer (Raw)

**Tables**: 2
**Purpose**: Raw ingestion from all sources
**Retention**: 30-90 days

- `bronze_transactions` - Raw transaction JSONB
- `bronze_products` - Raw product catalog JSONB

**Ingestion**:
- Daily batch: Airflow DAG at 2 AM UTC
- Real-time: n8n webhook `/scout-transactions`

### Silver Layer (Validated)

**Tables**: 2
**Purpose**: Schema-enforced, validated data
**Retention**: 2 years

- `silver_validated_transactions` - Cleaned transactions with validation
- `silver_products` - Deduplicated product catalog

**Validation Rules**:
- Amount > 0
- Date <= CURRENT_DATE
- Category in allowed list
- No duplicate transaction IDs

**Refresh**: Hourly via Airflow DAG

### Gold Layer (Business Marts)

**Tables**: 2
**Purpose**: Pre-aggregated analytics
**Retention**: 5 years

- `gold_monthly_summary` - Monthly totals by category
- `gold_category_trends` - Weekly trends with anomaly detection

**Metrics**:
- MoM/YoY growth rates
- Moving averages
- Anomaly detection (>2σ)

**Refresh**: Every 6 hours

### Platinum Layer (AI-Ready)

**Views**: 2
**Purpose**: ML features and embeddings
**Retention**: 90 days (regenerated)

- `platinum_transaction_embeddings` - Text for embedding generation
- `platinum_product_recommendations` - Collaborative filtering features

**Use Cases**:
- Semantic search (Genie)
- RAG context for LLMs
- Product recommendations
- Spend pattern analysis

## Orchestration

### Airflow DAGs

**`scout_ingestion_dag`** (Daily at 2 AM UTC):
```
fetch_google_drive → fetch_csv → validate → trigger_dbt_bronze → notify
```

**`scout_transformation_dag`** (Hourly):
```
check_bronze_freshness → run_dbt_silver → test_silver → validate_silver
→ run_dbt_gold → test_gold → update_metadata → notify
```

**`data_quality_dag`** (Daily at 8 AM UTC):
```
run_dbt_tests → calculate_dq_scores → check_thresholds → [send_alert | skip]
→ update_dashboard
```

### n8n Workflows

**Real-Time Transaction Ingestion**:
- Webhook: `POST /webhook/scout-transactions`
- Insert to Bronze → Validate → Trigger dbt Silver
- Response: 200 OK with batch_id

**Odoo Sync** (Future):
- Schedule: Every 15 minutes
- Fetch invoices → Insert Bronze → Trigger dbt

**Quality Alerts**:
- Trigger: DQ score <80%
- Action: Mattermost notification
- Escalation: Email to data-engineering@

## Data Quality

### 8-Step Validation Cycle

1. **Syntax**: JSON valid, types correct
2. **Type**: amount > 0, dates valid
3. **Lint**: SQL style, naming
4. **Security**: RLS policies enforced
5. **Test**: dbt tests pass (≥80% Silver, 100% Gold)
6. **Performance**: Query latency <3s
7. **Documentation**: 100% model coverage
8. **Integration**: >95% pipeline success (7d)

### Quality Scores

| Layer | Completeness | Uniqueness | Timeliness | Overall |
|-------|--------------|------------|------------|---------|
| Bronze | ≥99% | N/A | <5 min | N/A |
| Silver | ≥95% | 100% | <1 hour | ≥95% |
| Gold | 100% | 100% | <6 hours | 100% |
| Platinum | 100% | 100% | On-demand | 100% |

### Running Tests

```bash
# dbt tests
cd dbt-workbench
dbt test --target prod

# SQL tests
psql "$POSTGRES_URL" -f quality/tests/row_count_checks.sql
psql "$POSTGRES_URL" -f quality/tests/null_checks.sql

# Airflow DQ DAG
airflow dags trigger data_quality_validation
```

## Monitoring

### Key Metrics

```sql
-- Data freshness
SELECT
    schema_name,
    table_name,
    MAX(last_updated) AS last_refresh,
    EXTRACT(EPOCH FROM (NOW() - MAX(last_updated))) / 3600 AS hours_old
FROM ip_workbench.tables
GROUP BY schema_name, table_name
ORDER BY hours_old DESC;

-- Row counts by layer
SELECT
    'bronze' AS layer,
    COUNT(*) AS row_count
FROM scout.bronze_transactions
UNION ALL
SELECT 'silver', COUNT(*)
FROM scout.silver_validated_transactions
UNION ALL
SELECT 'gold', COUNT(*)
FROM scout.gold_monthly_summary;

-- DQ scores
SELECT
    schema_name || '.' || table_name AS table_name,
    dq_score,
    last_updated
FROM ip_workbench.tables
WHERE dq_score IS NOT NULL
ORDER BY dq_score ASC;
```

### Alerts

- **Mattermost**: https://mattermost.insightpulseai.net/hooks/...
- **Email**: alerts@insightpulseai.net
- **Threshold**: DQ score <80%

## Deployment

### Production Workflow

```bash
# 1. Validate changes
cd dbt-workbench
dbt compile
dbt test

# 2. Deploy to production
dbt run --target prod

# 3. Verify deployment
dbt test --target prod

# 4. Generate documentation
dbt docs generate

# 5. Upload to DO Spaces
aws s3 sync target/ s3://dbt-docs-bucket/ --endpoint-url=https://sgp1.digitaloceanspaces.com
```

### CI/CD Integration

```yaml
# GitHub Actions example
name: Deploy Data Layer
on:
  push:
    branches: [main]
    paths: ['data-layer/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dbt
        run: pip install dbt-postgres
      - name: Run dbt
        run: |
          cd dbt-workbench
          dbt run --target prod
          dbt test --target prod
```

## Integration Points

### AI Workbench (Frontend)

```typescript
// Query Gold layer via PostgREST
const { data } = await supabase
  .from('gold_monthly_summary')
  .select('*')
  .eq('month', '2025-12-01');
```

### Genie (NL2SQL)

```python
# Genie uses Platinum views for context
context = supabase.table('platinum_transaction_embeddings')
  .select('text, metadata')
  .limit(10)
  .execute()
```

### Apache Superset

```sql
-- Dashboard query (Gold layer)
SELECT
    month,
    category,
    total_amount,
    mom_growth_pct
FROM scout.gold_monthly_summary
WHERE month >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '12 months')
ORDER BY month DESC, total_amount DESC;
```

## Troubleshooting

### Connection Issues

**Symptom**: `dbt debug` fails

**Solution**:
```bash
# Use pooler port 6543, not direct 5432
export SUPABASE_PORT=6543

# Use service role key for dbt
export POSTGRES_PASSWORD=$SUPABASE_SERVICE_ROLE_KEY
```

### RLS Blocking Queries

**Symptom**: `SELECT` returns 0 rows for admin

**Solution**:
```sql
-- Disable RLS for dbt/Airflow
ALTER TABLE scout.bronze_transactions DISABLE ROW LEVEL SECURITY;
```

### Slow Transformations

**Symptom**: `dbt run` takes >10 minutes

**Solution**:
```bash
# Reduce thread count
dbt run --threads 2

# Use incremental models
dbt run --models silver+ --full-refresh
```

### Failed Tests

**Symptom**: `dbt test` fails with >100 errors

**Solution**:
```bash
# Store failures for analysis
dbt test --store-failures

# View failures
psql "$POSTGRES_URL" -c "SELECT * FROM test_failures.silver_validated_transactions LIMIT 10;"

# Fix data quality issues in Bronze layer
```

## Performance Optimization

### Indexes

All critical indexes are created via dbt post-hooks:
- Date columns (time-series queries)
- Foreign keys (joins)
- Category columns (grouping)
- Unique constraints (deduplication)

### Query Optimization

```sql
-- Use EXPLAIN ANALYZE
EXPLAIN ANALYZE
SELECT * FROM scout.gold_monthly_summary
WHERE month >= '2025-01-01';

-- Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan
FROM pg_stat_user_indexes
WHERE schemaname = 'scout'
ORDER BY idx_scan DESC;
```

## References

- [AI Workbench PRD](../spec-kit/spec/ai-workbench/prd.md)
- [Tasks Document](../spec-kit/spec/ai-workbench/tasks.md)
- [dbt Documentation](https://docs.getdbt.com/)
- [Airflow Documentation](https://airflow.apache.org/docs/)
- [n8n Documentation](https://docs.n8n.io/)
- [Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture)

## Support

- **Issues**: GitHub Issues
- **Slack**: #data-engineering
- **Email**: data-engineering@insightpulseai.net
