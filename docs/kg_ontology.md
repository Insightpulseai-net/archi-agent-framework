# Knowledge Graph Ontology

**Purpose**: Define the canonical node types and edge types for the InsightPulseAI AI Workbench knowledge graph.

**Version**: 1.0.0
**Last Updated**: 2025-12-09

---

## Node Types

| Type | Description | Example |
|------|-------------|---------|
| `repo` | Git repository containing code, specs, or documentation | `archi-agent-framework` |
| `spec_kit` | Specification bundle (constitution, PRD, plan, tasks) | `supabase-core`, `n8n-automation-hub` |
| `service` | Deployed application or infrastructure component | `supabase-postgres-core`, `n8n-automation-hub` |
| `workflow` | Automated process or pipeline | `kg-drift-monitor-workflow`, `spec-to-deployment-pipeline` |
| `agent` | AI agent or autonomous process | `kg-indexer-agent`, `kg-drift-monitor-agent` |
| `skill` | Specialized capability or function | `schema_introspection`, `drift_alerting` |
| `dataset` | Data source or database | `supabase_public_schema`, `knowledge_graph_data` |
| `environment` | Deployment target or runtime environment | `supabase_project_spdtwktxdalcfigzeqrz`, `digitalocean_app_platform` |

---

## Edge Types

| Type | From Type → To Type | Description |
|------|---------------------|-------------|
| `implements` | `spec_kit` → `service` | Spec Kit defines/implements a service or workflow |
| `depends_on` | `service\|workflow` → `service\|dataset` | Service/workflow requires another service or data source |
| `runs_on` | `service\|workflow` → `environment` | Service/workflow is deployed to an environment |
| `exposes` | `service` → `service` (capability) | Service exposes API endpoints or capabilities |
| `uses_agent` | `workflow\|service` → `agent` | Workflow/service utilizes an AI agent |
| `has_skill` | `agent` → `skill` | Agent possesses a specialized skill |
| `documents` | `spec_kit` → `repo\|service\|workflow` | Spec Kit provides documentation for a component |

---

## Design Principles

1. **Simplicity**: Minimal ontology covering high-value relationships
2. **Extensibility**: Can add node/edge types as system evolves
3. **Traceability**: Each node links to source (spec_kit, code, deployment)
4. **Automation-Ready**: Node/edge types map to ingestion pipelines

---

## Usage Examples

### Query: Find all services implemented by a Spec Kit
```sql
SELECT
  n.slug AS service_slug,
  n.title AS service_title
FROM kg.edges e
JOIN kg.nodes n ON n.slug = e.dst_slug
WHERE e.src_slug = 'supabase-core'
  AND e.type = 'implements';
```

### Query: Find all dependencies for a service
```sql
SELECT
  n.slug AS dependency_slug,
  n.type AS dependency_type,
  n.title AS dependency_title
FROM kg.edges e
JOIN kg.nodes n ON n.slug = e.dst_slug
WHERE e.src_slug = 'supabase-postgres-core'
  AND e.type = 'depends_on';
```

### Query: Find all agents and their skills
```sql
SELECT
  a.slug AS agent_slug,
  a.title AS agent_title,
  s.slug AS skill_slug,
  s.title AS skill_title
FROM kg.nodes a
JOIN kg.edges e ON e.src_slug = a.slug
JOIN kg.nodes s ON s.slug = e.dst_slug
WHERE a.type = 'agent'
  AND e.type = 'has_skill';
```

---

## Future Extensions

- **Node Types**: `deployment`, `migration`, `test_suite`, `dashboard`
- **Edge Types**: `triggers`, `monitors`, `validates`, `deploys_to`
- **Properties**: Add `version`, `status`, `last_sync` to node metadata
