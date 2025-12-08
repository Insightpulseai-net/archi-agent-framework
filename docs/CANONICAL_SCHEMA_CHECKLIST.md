# Canonical Schema Compliance Checklist

**Purpose**: Enforce data layer consistency and prevent schema drift.

**When to Use**: Before merging any database change (migrations, schema updates, new tables).

---

## Pre-Merge Checklist

### 1. Location & Source of Truth

- [ ] Change is reflected in `docs/DATA_MODEL.md`
- [ ] Change is implemented in `packages/db/sql/*.sql`
- [ ] No ad-hoc DDL outside canonical SQL files
- [ ] Migration file follows naming convention: `NN_descriptive_name.sql`

### 2. Naming & Types

- [ ] All identifiers are `snake_case` (tables, columns, functions)
- [ ] ID fields use `uuid PRIMARY KEY DEFAULT gen_random_uuid()`
- [ ] Timestamps use `timestamptz DEFAULT now()`
- [ ] Embeddings use `vector(1536)` with accompanying `model text` column
- [ ] Freeform/config fields are `jsonb` (e.g., `metadata`, `config`, `props`)
- [ ] No ambiguous abbreviations (e.g., `uid` → use `user_id`)

**Examples:**
```sql
✅ user_id uuid NOT NULL
✅ created_at timestamptz DEFAULT now()
✅ embedding vector(1536)
✅ metadata jsonb DEFAULT '{}'::jsonb

❌ userId uuid NOT NULL           -- camelCase
❌ created timestamp               -- missing 'tz'
❌ embedding vector(512)           -- wrong dimension
❌ metadata text                   -- should be jsonb
```

### 3. Multi-Tenancy & RLS

- [ ] Table has `tenant_id uuid NOT NULL` column
- [ ] Table has `workspace_id uuid` column if workspace-scoped
- [ ] RLS policy enforces tenant isolation:
  ```sql
  WHERE tenant_id = current_setting('app.current_tenant_id')::uuid
  AND workspace_id = current_setting('app.current_workspace_id')::uuid
  ```
- [ ] `set_tenant_context(tenant_uuid, workspace_uuid)` is sufficient to see only that tenant's rows
- [ ] Foreign key constraints include `tenant_id` for cross-table consistency

**RLS Policy Template:**
```sql
ALTER TABLE your_table ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON your_table
  USING (
    tenant_id = current_setting('app.current_tenant_id', true)::uuid
    AND workspace_id = current_setting('app.current_workspace_id', true)::uuid
  );
```

### 4. Relationships

- [ ] All foreign keys follow canonical entity graph:
  ```
  tenants (1) → (*) workspaces
  workspaces (1) → (*) agents
  agents (1) → (*) agent_runs
  agents (*) ←→ (*) skills (via agent_skills junction)
  ```
- [ ] RAG tables reference `tenant_id`, `workspace_id`, and parent tables correctly:
  ```
  rag_sources → rag_documents → rag_chunks → rag_embeddings
  rag_queries, rag_evaluations, llm_requests
  ```
- [ ] KG relationships use `kg.nodes.slug` as external key (not `id`)
- [ ] No "shadow" tables duplicating canonical entities

**Foreign Key Examples:**
```sql
✅ workspace_id uuid REFERENCES workspaces(id) ON DELETE CASCADE
✅ agent_id uuid REFERENCES agents(id) ON DELETE CASCADE
✅ src_slug text REFERENCES kg.nodes(slug) ON DELETE CASCADE

❌ workspace uuid REFERENCES workspaces(id)  -- missing _id suffix
❌ agent_id uuid REFERENCES agents(id)       -- missing ON DELETE
```

### 5. RAG & KG Rules

- [ ] New RAG tables follow pattern: `rag_*` prefix with consistent naming
- [ ] RAG embeddings table includes:
  - `embedding vector(1536)`
  - `model text DEFAULT 'text-embedding-3-small'`
  - `chunk_id` foreign key to `rag_chunks`
- [ ] New KG tables live under `kg.*` schema (or extend `kg.nodes`/`kg.edges`)
- [ ] KG nodes use `slug text UNIQUE NOT NULL` as external identifier
- [ ] KG edges use `(src_slug, dst_slug, type)` as compound unique key

**KG Node Template:**
```sql
INSERT INTO kg.nodes (slug, type, title, description, props, metadata)
VALUES (
  'node:identifier',           -- Canonical slug format: type:identifier
  'canonical_type',            -- From 15 canonical types
  'Display Title',
  'Description text',
  jsonb_build_object('key', 'value'),
  jsonb_build_object('key', 'value')
) ON CONFLICT (slug) DO NOTHING;
```

### 6. Indexing & Performance

- [ ] Foreign key columns have indexes
- [ ] Lookup fields (slug, type, status) have indexes
- [ ] Vector columns use IVFFlat indexing:
  ```sql
  CREATE INDEX idx_nodes_embedding ON kg.nodes
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
  ```
- [ ] Composite indexes for multi-column WHERE clauses:
  ```sql
  CREATE INDEX idx_table_tenant_workspace
  ON table_name(tenant_id, workspace_id);
  ```

### 7. Validation & Testing

- [ ] `make db-all` completes without errors
- [ ] `make db-smoke` confirms:
  - All canonical tables exist
  - RLS enabled where required
  - Indexes created for FKs and lookup fields
  - Seed data inserted correctly
- [ ] `make validate-schema` passes (if implemented)
- [ ] Manual RLS test:
  ```sql
  SELECT set_tenant_context('test-tenant-uuid', 'test-workspace-uuid');
  SELECT COUNT(*) FROM your_table;  -- Should only see tenant's rows
  ```

---

## Canonical Entity Reference

### Core Entities (`04_core_entities.sql`)
```
tenants          → Root multi-tenant table
workspaces       → Organizational units within tenant
agents           → LangGraph agents (workspace-scoped)
agent_runs       → Agent execution history
skills           → Agent capabilities
agent_skills     → Many-to-many junction (agent ↔ skill)
```

### RAG Entities (`05_rag_entities.sql`)
```
rag_sources      → Document sources (GitHub, URLs, files)
rag_documents    → Parsed documents
rag_chunks       → Document segments for embedding
rag_embeddings   → Vector embeddings (1536 dimensions)
rag_queries      → User queries with results
rag_evaluations  → Quality metrics for RAG responses
llm_requests     → Token usage tracking
```

### Knowledge Graph (`02_kg_nodes_edges.sql`)
```
kg.nodes         → 15 canonical types (repository, service, database, etc.)
kg.edges         → 13 canonical types (uses_service, depends_on, etc.)
kg.ingestion_log → ETL audit trail
kg.schema_version → Migration tracking
```

---

## Common Violations & Fixes

### ❌ Violation: camelCase column names
```sql
CREATE TABLE users (
  userId uuid PRIMARY KEY,        -- Wrong
  firstName text,                 -- Wrong
  createdAt timestamp             -- Wrong
);
```

### ✅ Fix: snake_case everywhere
```sql
CREATE TABLE users (
  user_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  first_name text,
  created_at timestamptz DEFAULT now()
);
```

---

### ❌ Violation: Missing RLS
```sql
CREATE TABLE sensitive_data (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL,
  data text
);
-- No RLS policy defined!
```

### ✅ Fix: Enable RLS with tenant isolation
```sql
CREATE TABLE sensitive_data (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  workspace_id uuid NOT NULL,
  data text,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE sensitive_data ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON sensitive_data
  USING (
    tenant_id = current_setting('app.current_tenant_id', true)::uuid
    AND workspace_id = current_setting('app.current_workspace_id', true)::uuid
  );
```

---

### ❌ Violation: Shadow tables (duplicate canonical entities)
```sql
-- Creating duplicate agent tracking
CREATE TABLE my_custom_agents (
  id uuid PRIMARY KEY,
  name text,
  config jsonb
);
```

### ✅ Fix: Extend canonical agents table
```sql
-- Add custom fields to canonical agents table
ALTER TABLE agents ADD COLUMN custom_config jsonb DEFAULT '{}'::jsonb;

-- OR use metadata field
UPDATE agents
SET metadata = metadata || jsonb_build_object('custom_key', 'value')
WHERE id = 'agent-uuid';
```

---

### ❌ Violation: Wrong embedding dimensions
```sql
CREATE TABLE documents (
  id uuid PRIMARY KEY,
  embedding vector(512)  -- Wrong dimension
);
```

### ✅ Fix: Use canonical 1536 dimensions
```sql
CREATE TABLE documents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  embedding vector(1536),  -- OpenAI text-embedding-3-small
  model text DEFAULT 'text-embedding-3-small',
  created_at timestamptz DEFAULT now()
);
```

---

## CI/CD Integration

### GitHub Actions Workflow
```yaml
name: Canonical Schema Validation

on:
  pull_request:
    paths:
      - 'packages/db/sql/**'
      - 'docs/DATA_MODEL.md'

jobs:
  validate-schema:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup PostgreSQL
        uses: ikalnytskyi/action-setup-postgres@v4
        with:
          postgres-version: '15'

      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y postgresql-15-pgvector

      - name: Run schema validation
        env:
          POSTGRES_URL: ${{ secrets.DATABASE_URL }}
        run: |
          make db-reset
          make db-all
          make db-smoke
          make validate-schema
```

---

## Manual Review Guidance

When reviewing DB PRs, check:

1. **Documentation First**
   - Is `DATA_MODEL.md` updated with new tables/columns?
   - Does the PR description explain WHY the schema change is needed?

2. **Migration Safety**
   - Are migrations idempotent (safe to re-run)?
   - Do migrations handle existing data gracefully?
   - Are DROP operations avoided or carefully justified?

3. **Naming Audit**
   - Run: `grep -r "camelCase\|PascalCase" packages/db/sql/` (should be empty)
   - Check all column names match `snake_case` convention

4. **RLS Audit**
   - Run: `psql -c "\d+ table_name"` and verify "Policies" section exists
   - Test with: `SELECT set_tenant_context(...); SELECT * FROM table_name;`

5. **Relationship Integrity**
   - Verify foreign keys with: `psql -c "\d+ table_name"` (check "Referenced by" section)
   - Check cascade rules are appropriate (`ON DELETE CASCADE` vs `RESTRICT`)

---

## Quick Commands

```bash
# Validate entire schema
make db-reset && make db-all && make db-smoke

# Check for naming violations
grep -rE "[a-z][A-Z]" packages/db/sql/*.sql

# List all tables without RLS
psql "$POSTGRES_URL" -c "
  SELECT schemaname, tablename
  FROM pg_tables
  WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
  AND tablename NOT IN (
    SELECT tablename FROM pg_policies
  );
"

# Verify RLS is enforced
psql "$POSTGRES_URL" -c "
  SELECT tablename, rowsecurity
  FROM pg_tables
  WHERE schemaname = 'public' OR schemaname = 'kg';
"
```

---

## Sign-Off

**Before merging, confirm:**
- [ ] All checklist items above are complete
- [ ] Canonical schema auditor prompt has reviewed changes (if automated)
- [ ] CI schema validation passes
- [ ] PR reviewer has manually verified RLS and naming compliance

**Reviewer signature:** _______________
**Date:** _______________

---

## References

- **Canonical Schema Specification**: `docs/DATA_MODEL.md`
- **Canonical SQL Implementation**: `packages/db/sql/*.sql`
- **Deployment Guide**: `docs/kg_schema_deployment.md`
- **Makefile Targets**: `Makefile` (db-all, db-smoke, validate-schema)
