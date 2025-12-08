# Data Model — Canonical Naming & Entity Definitions

**Last Updated**: 2025-12-09
**Status**: Canonical Reference
**Purpose**: Define naming conventions, entity relationships, and multi-tenant patterns for the archi-agent-framework database.

---

## 1. Canonical Naming Conventions

### Schemas
- **`public`**: Operational/core tables (tenants, workspaces, agents, tasks)
- **`kg`**: Knowledge graph (nodes, edges, ingestion_log)
- **`rag`** (optional): RAG-specific tables (rag_sources, rag_documents, rag_chunks, rag_embeddings)

### Tables
- **Format**: `snake_case`, **plural** (e.g., `tenants`, `workspaces`, `agents`, `agent_runs`)
- **Anti-pattern**: Singular tables (`agent`, `skill`) or camelCase (`agentRuns`)

### Columns
- **Primary Key**: `id` (uuid, NOT NULL, DEFAULT gen_random_uuid())
- **Foreign Keys**: `<table_singular>_id` (e.g., `tenant_id`, `workspace_id`, `agent_id`)
- **Timestamps**: `created_at` (timestamptz, NOT NULL, DEFAULT now()), `updated_at` (timestamptz, NOT NULL, DEFAULT now())
- **Soft Deletes** (optional): `deleted_at` (timestamptz, NULL)

### Multi-Tenant Patterns
- **Always include**: `tenant_id` (uuid NOT NULL REFERENCES tenants(id))
- **Workspace-scoped**: `workspace_id` (uuid NOT NULL REFERENCES workspaces(id))
- **RLS Policies**: Enable Row-Level Security on all public tables with tenant_id filters

---

## 2. Core Entities (DM/Bus Layer)

### `tenants`
**Purpose**: Top-level organization/account isolation

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PK | Tenant unique identifier |
| `name` | text | NOT NULL | Organization name |
| `slug` | text | UNIQUE NOT NULL | URL-safe identifier |
| `settings` | jsonb | DEFAULT '{}' | Tenant-level configuration |
| `created_at` | timestamptz | NOT NULL | Creation timestamp |
| `updated_at` | timestamptz | NOT NULL | Last update timestamp |

**RLS**: Tenants can only see their own data via `tenant_id` filter.

---

### `workspaces`
**Purpose**: Sub-organization grouping (projects, teams, environments)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PK | Workspace unique identifier |
| `tenant_id` | uuid | FK → tenants(id) | Parent tenant |
| `name` | text | NOT NULL | Workspace display name |
| `slug` | text | NOT NULL | URL-safe identifier (unique per tenant) |
| `settings` | jsonb | DEFAULT '{}' | Workspace-level configuration |
| `created_at` | timestamptz | NOT NULL | Creation timestamp |
| `updated_at` | timestamptz | NOT NULL | Last update timestamp |

**Unique Constraint**: `(tenant_id, slug)` to prevent duplicate workspace slugs within a tenant.

---

### `agents`
**Purpose**: Registered AI agents/personas (e.g., kg-indexer-agent, drift-monitor-agent)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PK | Agent unique identifier |
| `tenant_id` | uuid | FK → tenants(id) | Parent tenant |
| `workspace_id` | uuid | FK → workspaces(id) | Parent workspace |
| `name` | text | NOT NULL | Agent display name |
| `slug` | text | NOT NULL | URL-safe identifier (unique per workspace) |
| `description` | text | NULL | Agent purpose/capabilities |
| `agent_type` | text | NOT NULL | Agent category (indexing, monitoring, workflow) |
| `config` | jsonb | DEFAULT '{}' | Agent-specific configuration (model, parameters) |
| `status` | text | DEFAULT 'active' | Agent status (active, paused, archived) |
| `created_at` | timestamptz | NOT NULL | Creation timestamp |
| `updated_at` | timestamptz | NOT NULL | Last update timestamp |

**Unique Constraint**: `(workspace_id, slug)` to prevent duplicate agent slugs within a workspace.

---

### `agent_runs`
**Purpose**: Individual agent execution logs (traces, metrics, results)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PK | Run unique identifier |
| `agent_id` | uuid | FK → agents(id) | Parent agent |
| `tenant_id` | uuid | FK → tenants(id) | Parent tenant |
| `workspace_id` | uuid | FK → workspaces(id) | Parent workspace |
| `status` | text | DEFAULT 'pending' | Run status (pending, running, completed, failed) |
| `trigger` | text | NULL | Run trigger (manual, scheduled, webhook) |
| `input_params` | jsonb | DEFAULT '{}' | Run input parameters |
| `results` | jsonb | DEFAULT '{}' | Run output results |
| `error_message` | text | NULL | Error details (if failed) |
| `started_at` | timestamptz | NULL | Run start timestamp |
| `completed_at` | timestamptz | NULL | Run completion timestamp |
| `created_at` | timestamptz | NOT NULL | Creation timestamp |
| `updated_at` | timestamptz | NOT NULL | Last update timestamp |

**Indexes**:
- `(agent_id, created_at DESC)` for agent run history
- `(status, started_at)` for active run monitoring

---

### `skills`
**Purpose**: Atomic capabilities/functions (e.g., schema-introspection, drift-alerting)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PK | Skill unique identifier |
| `tenant_id` | uuid | FK → tenants(id) | Parent tenant |
| `name` | text | NOT NULL | Skill display name |
| `slug` | text | UNIQUE NOT NULL | URL-safe identifier |
| `description` | text | NULL | Skill purpose/capabilities |
| `skill_type` | text | NOT NULL | Skill category (data_access, transformation, alerting) |
| `implementation` | text | NULL | Implementation reference (function name, API endpoint) |
| `config` | jsonb | DEFAULT '{}' | Skill-specific configuration |
| `created_at` | timestamptz | NOT NULL | Creation timestamp |
| `updated_at` | timestamptz | NOT NULL | Last update timestamp |

**Unique Constraint**: `slug` globally unique across tenants.

---

### `agent_skills`
**Purpose**: Many-to-many relationship between agents and skills

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PK | Relationship unique identifier |
| `agent_id` | uuid | FK → agents(id) | Parent agent |
| `skill_id` | uuid | FK → skills(id) | Associated skill |
| `tenant_id` | uuid | FK → tenants(id) | Parent tenant |
| `is_required` | boolean | DEFAULT false | Whether skill is required for agent operation |
| `config_override` | jsonb | DEFAULT '{}' | Agent-specific skill configuration |
| `created_at` | timestamptz | NOT NULL | Creation timestamp |

**Unique Constraint**: `(agent_id, skill_id)` to prevent duplicate skill assignments.

---

## 3. RAG Entities (Optional Schema)

### `rag.rag_sources`
**Purpose**: External data sources for RAG ingestion (repos, docs, APIs)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PK | Source unique identifier |
| `tenant_id` | uuid | FK → tenants(id) | Parent tenant |
| `workspace_id` | uuid | FK → workspaces(id) | Parent workspace |
| `name` | text | NOT NULL | Source display name |
| `source_type` | text | NOT NULL | Source type (github, confluence, gdrive, url) |
| `source_url` | text | NOT NULL | Source location/URL |
| `config` | jsonb | DEFAULT '{}' | Source-specific configuration (auth, filters) |
| `status` | text | DEFAULT 'active' | Source status (active, paused, error) |
| `last_synced_at` | timestamptz | NULL | Last successful sync timestamp |
| `created_at` | timestamptz | NOT NULL | Creation timestamp |
| `updated_at` | timestamptz | NOT NULL | Last update timestamp |

---

### `rag.rag_documents`
**Purpose**: Individual documents from RAG sources

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PK | Document unique identifier |
| `rag_source_id` | uuid | FK → rag_sources(id) | Parent source |
| `tenant_id` | uuid | FK → tenants(id) | Parent tenant |
| `workspace_id` | uuid | FK → workspaces(id) | Parent workspace |
| `title` | text | NOT NULL | Document title/name |
| `doc_type` | text | NOT NULL | Document type (markdown, pdf, code, api_doc) |
| `source_path` | text | NOT NULL | Document path/URL within source |
| `content` | text | NULL | Raw document content |
| `metadata` | jsonb | DEFAULT '{}' | Document metadata (author, version, tags) |
| `status` | text | DEFAULT 'indexed' | Document status (indexed, processing, error) |
| `created_at` | timestamptz | NOT NULL | Creation timestamp |
| `updated_at` | timestamptz | NOT NULL | Last update timestamp |

**Unique Constraint**: `(rag_source_id, source_path)` to prevent duplicate documents.

---

### `rag.rag_chunks`
**Purpose**: Text chunks for vector embedding (semantic search units)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PK | Chunk unique identifier |
| `rag_document_id` | uuid | FK → rag_documents(id) | Parent document |
| `tenant_id` | uuid | FK → tenants(id) | Parent tenant |
| `workspace_id` | uuid | FK → workspaces(id) | Parent workspace |
| `chunk_index` | integer | NOT NULL | Chunk sequence number within document |
| `content` | text | NOT NULL | Chunk text content |
| `char_start` | integer | NULL | Start character position in document |
| `char_end` | integer | NULL | End character position in document |
| `metadata` | jsonb | DEFAULT '{}' | Chunk metadata (section, headers, code_language) |
| `created_at` | timestamptz | NOT NULL | Creation timestamp |

**Unique Constraint**: `(rag_document_id, chunk_index)` to prevent duplicate chunks.
**Index**: `(rag_document_id, chunk_index)` for ordered chunk retrieval.

---

### `rag.rag_embeddings`
**Purpose**: Vector embeddings for semantic search

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PK | Embedding unique identifier |
| `rag_chunk_id` | uuid | FK → rag_chunks(id) | Parent chunk |
| `tenant_id` | uuid | FK → tenants(id) | Parent tenant |
| `workspace_id` | uuid | FK → workspaces(id) | Parent workspace |
| `embedding` | vector(1536) | NOT NULL | OpenAI text-embedding-3-small vector |
| `model` | text | DEFAULT 'text-embedding-3-small' | Embedding model used |
| `created_at` | timestamptz | NOT NULL | Creation timestamp |

**Unique Constraint**: `rag_chunk_id` (one embedding per chunk).
**Index**: `embedding vector_cosine_ops` for similarity search (HNSW index).

---

### `rag.rag_queries`
**Purpose**: User RAG queries for analytics and evaluation

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PK | Query unique identifier |
| `agent_run_id` | uuid | FK → agent_runs(id) | Parent agent run (optional) |
| `tenant_id` | uuid | FK → tenants(id) | Parent tenant |
| `workspace_id` | uuid | FK → workspaces(id) | Parent workspace |
| `query_text` | text | NOT NULL | User query text |
| `query_embedding` | vector(1536) | NULL | Query embedding vector |
| `results` | jsonb | DEFAULT '[]' | Retrieved chunks and similarity scores |
| `response_text` | text | NULL | Generated response text |
| `created_at` | timestamptz | NOT NULL | Creation timestamp |

**Index**: `(tenant_id, created_at DESC)` for query history.

---

### `rag.rag_evaluations`
**Purpose**: RAG quality metrics (relevance, accuracy, user feedback)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PK | Evaluation unique identifier |
| `rag_query_id` | uuid | FK → rag_queries(id) | Parent query |
| `tenant_id` | uuid | FK → tenants(id) | Parent tenant |
| `workspace_id` | uuid | FK → workspaces(id) | Parent workspace |
| `metric_type` | text | NOT NULL | Metric type (relevance, accuracy, user_feedback) |
| `score` | numeric(3,2) | NULL | Metric score (0.00-1.00) |
| `feedback` | text | NULL | User feedback text |
| `metadata` | jsonb | DEFAULT '{}' | Evaluation metadata (ground_truth, context) |
| `created_at` | timestamptz | NOT NULL | Creation timestamp |

---

### `rag.llm_requests`
**Purpose**: LLM API call logs (usage tracking, debugging)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PK | Request unique identifier |
| `agent_run_id` | uuid | FK → agent_runs(id) | Parent agent run (optional) |
| `rag_query_id` | uuid | FK → rag_queries(id) | Parent RAG query (optional) |
| `tenant_id` | uuid | FK → tenants(id) | Parent tenant |
| `workspace_id` | uuid | FK → workspaces(id) | Parent workspace |
| `provider` | text | NOT NULL | LLM provider (openai, anthropic, azure) |
| `model` | text | NOT NULL | Model name (gpt-4, claude-3-sonnet) |
| `prompt_tokens` | integer | NULL | Input token count |
| `completion_tokens` | integer | NULL | Output token count |
| `total_tokens` | integer | NULL | Total token count |
| `latency_ms` | integer | NULL | API response time (milliseconds) |
| `status` | text | DEFAULT 'success' | Request status (success, error, timeout) |
| `error_message` | text | NULL | Error details (if failed) |
| `created_at` | timestamptz | NOT NULL | Creation timestamp |

**Indexes**:
- `(tenant_id, created_at DESC)` for usage analytics
- `(provider, model, created_at DESC)` for cost tracking

---

## 4. Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    tenants ||--o{ workspaces : "has many"
    tenants ||--o{ agents : "has many"
    tenants ||--o{ agent_runs : "has many"
    tenants ||--o{ skills : "has many"
    tenants ||--o{ rag_sources : "has many"

    workspaces ||--o{ agents : "contains"
    workspaces ||--o{ agent_runs : "contains"
    workspaces ||--o{ rag_sources : "contains"

    agents ||--o{ agent_runs : "executes"
    agents ||--o{ agent_skills : "has capabilities"

    skills ||--o{ agent_skills : "used by agents"

    agent_runs ||--o{ rag_queries : "performs"
    agent_runs ||--o{ llm_requests : "makes API calls"

    rag_sources ||--o{ rag_documents : "contains"
    rag_documents ||--o{ rag_chunks : "split into"
    rag_chunks ||--|| rag_embeddings : "has embedding"

    rag_queries ||--o{ rag_evaluations : "evaluated by"
    rag_queries ||--o{ llm_requests : "triggers"

    tenants {
        uuid id PK
        text name
        text slug UK
        jsonb settings
        timestamptz created_at
        timestamptz updated_at
    }

    workspaces {
        uuid id PK
        uuid tenant_id FK
        text name
        text slug
        jsonb settings
        timestamptz created_at
        timestamptz updated_at
    }

    agents {
        uuid id PK
        uuid tenant_id FK
        uuid workspace_id FK
        text name
        text slug
        text description
        text agent_type
        jsonb config
        text status
        timestamptz created_at
        timestamptz updated_at
    }

    agent_runs {
        uuid id PK
        uuid agent_id FK
        uuid tenant_id FK
        uuid workspace_id FK
        text status
        text trigger
        jsonb input_params
        jsonb results
        text error_message
        timestamptz started_at
        timestamptz completed_at
        timestamptz created_at
        timestamptz updated_at
    }

    skills {
        uuid id PK
        uuid tenant_id FK
        text name
        text slug UK
        text description
        text skill_type
        text implementation
        jsonb config
        timestamptz created_at
        timestamptz updated_at
    }

    agent_skills {
        uuid id PK
        uuid agent_id FK
        uuid skill_id FK
        uuid tenant_id FK
        boolean is_required
        jsonb config_override
        timestamptz created_at
    }

    rag_sources {
        uuid id PK
        uuid tenant_id FK
        uuid workspace_id FK
        text name
        text source_type
        text source_url
        jsonb config
        text status
        timestamptz last_synced_at
        timestamptz created_at
        timestamptz updated_at
    }

    rag_documents {
        uuid id PK
        uuid rag_source_id FK
        uuid tenant_id FK
        uuid workspace_id FK
        text title
        text doc_type
        text source_path
        text content
        jsonb metadata
        text status
        timestamptz created_at
        timestamptz updated_at
    }

    rag_chunks {
        uuid id PK
        uuid rag_document_id FK
        uuid tenant_id FK
        uuid workspace_id FK
        integer chunk_index
        text content
        integer char_start
        integer char_end
        jsonb metadata
        timestamptz created_at
    }

    rag_embeddings {
        uuid id PK
        uuid rag_chunk_id FK UK
        uuid tenant_id FK
        uuid workspace_id FK
        vector embedding
        text model
        timestamptz created_at
    }

    rag_queries {
        uuid id PK
        uuid agent_run_id FK
        uuid tenant_id FK
        uuid workspace_id FK
        text query_text
        vector query_embedding
        jsonb results
        text response_text
        timestamptz created_at
    }

    rag_evaluations {
        uuid id PK
        uuid rag_query_id FK
        uuid tenant_id FK
        uuid workspace_id FK
        text metric_type
        numeric score
        text feedback
        jsonb metadata
        timestamptz created_at
    }

    llm_requests {
        uuid id PK
        uuid agent_run_id FK
        uuid rag_query_id FK
        uuid tenant_id FK
        uuid workspace_id FK
        text provider
        text model
        integer prompt_tokens
        integer completion_tokens
        integer total_tokens
        integer latency_ms
        text status
        text error_message
        timestamptz created_at
    }
```

---

## 5. Multi-Tenant Patterns

### Row-Level Security (RLS)

**Enable RLS on all public tables**:
```sql
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_skills ENABLE ROW LEVEL SECURITY;
```

**Example RLS Policy (tenants)**:
```sql
CREATE POLICY tenant_isolation ON tenants
  FOR ALL
  USING (id = current_setting('app.current_tenant_id')::uuid);
```

**Example RLS Policy (workspace-scoped)**:
```sql
CREATE POLICY workspace_isolation ON agents
  FOR ALL
  USING (
    tenant_id = current_setting('app.current_tenant_id')::uuid
    AND workspace_id = current_setting('app.current_workspace_id')::uuid
  );
```

### Application Context Setting

**Set tenant/workspace context before queries**:
```sql
-- Set tenant context
SET LOCAL app.current_tenant_id = 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx';

-- Set workspace context
SET LOCAL app.current_workspace_id = 'yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy';
```

**PostgreSQL Function (helper)**:
```sql
CREATE OR REPLACE FUNCTION set_tenant_context(tenant_uuid uuid, workspace_uuid uuid)
RETURNS void AS $
BEGIN
  PERFORM set_config('app.current_tenant_id', tenant_uuid::text, true);
  PERFORM set_config('app.current_workspace_id', workspace_uuid::text, true);
END;
$ LANGUAGE plpgsql;
```

---

## 6. Migration Strategy

### File Naming Convention
- Format: `##_descriptive_name.sql` (e.g., `04_core_entities.sql`, `05_rag_entities.sql`)
- Sequence: Schema changes → seed data → indexes → RLS policies

### Migration Order
1. **Core Entities** (`04_core_entities.sql`): tenants, workspaces, agents, agent_runs, skills, agent_skills
2. **RAG Entities** (`05_rag_entities.sql`): rag.rag_sources, rag_documents, rag_chunks, rag_embeddings, rag_queries, rag_evaluations, llm_requests
3. **Indexes** (`06_indexes.sql`): Performance optimization indexes
4. **RLS Policies** (`07_rls_policies.sql`): Row-level security policies

### Idempotency Pattern
```sql
-- Drop existing table if exists (for development only)
DROP TABLE IF EXISTS tenants CASCADE;

-- Create table
CREATE TABLE tenants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  slug text UNIQUE NOT NULL,
  settings jsonb DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Create trigger for updated_at
CREATE TRIGGER update_tenants_updated_at
  BEFORE UPDATE ON tenants
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();
```

---

## 7. Future Extensions

### Planned Additions
- **`workflows`** table for multi-step agent orchestration
- **`audit_logs`** table for compliance and change tracking
- **`api_keys`** table for external API authentication
- **`webhooks`** table for event notifications

### Analytics/Reporting (Future)
- Dimensional modeling: fact_agent_runs, dim_agents, dim_time
- Aggregation tables: daily_agent_metrics, workspace_usage_summary
- Materialized views for dashboard queries

---

## 8. References

- **Supabase Multi-Tenancy**: https://supabase.com/docs/guides/auth/row-level-security
- **PostgreSQL RLS**: https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- **pgvector Extension**: https://github.com/pgvector/pgvector
- **OpenAI Embeddings**: https://platform.openai.com/docs/guides/embeddings
