-- ============================================================================
-- Knowledge Graph: Initial Seed Data
-- ============================================================================
-- Purpose: Populate canonical nodes and edges for the InsightPulseAI AI Workbench ecosystem
-- Version: 1.0.0
-- Date: 2025-12-09
--
-- Ontology:
-- - 15 node types: product, service, database, schema, table, workflow, repository, spec_kit, module, dashboard, agent, skill, worktree_branch, migration, deployment
-- - 13 edge types: uses_service, depends_on, stores_data_in, has_dashboard, implements_spec, merged_from, deployed_to, triggers_workflow, has_migration, powers_agent, has_seed_data, enforces_rls, validated_by
--
-- Design Notes:
-- - All INSERT operations use ON CONFLICT DO NOTHING for idempotency
-- - Embeddings are NULL (will be populated by Edge Function or manual update)
-- - Metadata contains additional context for future extensibility
-- ============================================================================

BEGIN;

-- ============================================================================
-- REPOSITORIES
-- ============================================================================

INSERT INTO kg.nodes (slug, type, title, description, props, metadata) VALUES
(
  'repo:archi-agent-framework',
  'repository',
  'AI Workbench Framework Repository',
  'Core repository for the InsightPulseAI AI Workbench - multi-agent orchestration framework with knowledge graph, LiteLLM, and Supabase integration',
  jsonb_build_object(
    'url', 'https://github.com/jgtolentino/archi-agent-framework',
    'language', 'TypeScript',
    'stack', jsonb_build_array('Node.js', 'TypeScript', 'PostgreSQL', 'LangGraph')
  ),
  jsonb_build_object(
    'owner', 'jgtolentino',
    'visibility', 'private',
    'primary_maintainer', 'Jake Tolentino'
  )
)
ON CONFLICT (slug) DO NOTHING;

-- ============================================================================
-- SERVICES
-- ============================================================================

INSERT INTO kg.nodes (slug, type, title, description, props, metadata) VALUES
(
  'service:supabase-core',
  'service',
  'Supabase PostgreSQL Database',
  'Primary database service (project: xkxyvboeubffxxbebsll) hosting knowledge graph, RAG pipeline, and operational data',
  jsonb_build_object(
    'provider', 'Supabase',
    'type', 'PostgreSQL 15',
    'connection_string', 'aws-1-us-east-1.pooler.supabase.com:6543',
    'project_ref', 'xkxyvboeubffxxbebsll'
  ),
  jsonb_build_object(
    'region', 'us-east-1',
    'tier', 'Pro',
    'features', jsonb_build_array('pgvector', 'RLS', 'Edge Functions', 'Realtime')
  )
),
(
  'service:litellm-gateway',
  'service',
  'LiteLLM API Gateway',
  'Unified LLM gateway supporting OpenAI, Anthropic, and DeepSeek models with rate limiting and cost tracking',
  jsonb_build_object(
    'type', 'API Gateway',
    'supported_providers', jsonb_build_array('OpenAI', 'Anthropic', 'DeepSeek'),
    'features', jsonb_build_array('rate_limiting', 'cost_tracking', 'fallback_routing')
  ),
  jsonb_build_object(
    'deployment', 'self-hosted',
    'version', '1.x'
  )
),
(
  'service:vercel-hosting',
  'service',
  'Vercel Frontend Hosting',
  'Next.js application hosting for AI Workbench UI and catalog interfaces',
  jsonb_build_object(
    'provider', 'Vercel',
    'type', 'Next.js Hosting',
    'features', jsonb_build_array('edge_functions', 'analytics', 'preview_deployments')
  ),
  jsonb_build_object(
    'tier', 'Pro',
    'domain', 'workbench.insightpulseai.net'
  )
)
ON CONFLICT (slug) DO NOTHING;

-- ============================================================================
-- DATABASES & SCHEMAS
-- ============================================================================

INSERT INTO kg.nodes (slug, type, title, description, props, metadata) VALUES
(
  'database:knowledge-graph',
  'database',
  'Knowledge Graph Database',
  'PostgreSQL database with pgvector extension for semantic search and graph traversal',
  jsonb_build_object(
    'host', 'supabase',
    'extensions', jsonb_build_array('pgvector', 'uuid-ossp', 'pg_trgm'),
    'schemas', jsonb_build_array('kg', 'public', 'rag')
  ),
  jsonb_build_object(
    'version', 'PostgreSQL 15',
    'max_connections', 100
  )
),
(
  'schema:kg',
  'schema',
  'Knowledge Graph Schema',
  'Core schema containing nodes, edges, ingestion_log, and schema_version tables',
  jsonb_build_object(
    'tables', jsonb_build_array('nodes', 'edges', 'ingestion_log', 'schema_version'),
    'functions', jsonb_build_array('graph_search', 'graph_neighbors', 'graph_path', 'graph_context_for')
  ),
  jsonb_build_object(
    'migration_version', '02_kg_nodes_edges',
    'created_at', '2025-12-09'
  )
),
(
  'schema:public',
  'schema',
  'Operational Schema',
  'Core operational entities for multi-tenant agent orchestration',
  jsonb_build_object(
    'tables', jsonb_build_array('tenants', 'workspaces', 'agents', 'agent_runs', 'skills', 'agent_skills'),
    'rls_enabled', true
  ),
  jsonb_build_object(
    'migration_version', '04_core_entities',
    'created_at', '2025-12-09'
  )
),
(
  'schema:rag',
  'schema',
  'RAG Pipeline Schema',
  'Complete document ingestion, chunking, embedding, and query pipeline',
  jsonb_build_object(
    'tables', jsonb_build_array('rag_sources', 'rag_documents', 'rag_chunks', 'rag_embeddings', 'rag_queries', 'rag_evaluations', 'llm_requests'),
    'rls_enabled', true
  ),
  jsonb_build_object(
    'migration_version', '05_rag_entities',
    'created_at', '2025-12-09'
  )
)
ON CONFLICT (slug) DO NOTHING;

-- ============================================================================
-- MODULES & COMPONENTS
-- ============================================================================

INSERT INTO kg.nodes (slug, type, title, description, props, metadata) VALUES
(
  'module:agent-layer',
  'module',
  'LangGraph Agent Layer',
  'Multi-agent orchestration layer with specialized agents for different workflows',
  jsonb_build_object(
    'framework', 'LangGraph',
    'language', 'TypeScript',
    'agents', jsonb_build_array('research', 'sql-generator', 'code-reviewer', 'documentation')
  ),
  jsonb_build_object(
    'location', 'packages/agents/',
    'dependencies', jsonb_build_array('langchain', 'langgraph', '@supabase/supabase-js')
  )
),
(
  'module:vector-search',
  'module',
  'Vector Similarity Search Module',
  'Semantic search using pgvector with IVFFlat indexing for node embeddings',
  jsonb_build_object(
    'index_type', 'IVFFlat',
    'distance_metric', 'cosine',
    'dimensions', 1536
  ),
  jsonb_build_object(
    'location', 'packages/db/sql/02_kg_schema.sql',
    'function', 'kg.graph_search()'
  )
),
(
  'module:graph-traversal',
  'module',
  'Graph Traversal Module',
  'Multi-hop graph traversal with configurable depth and edge type filtering',
  jsonb_build_object(
    'max_depth', 5,
    'functions', jsonb_build_array('graph_neighbors', 'graph_path')
  ),
  jsonb_build_object(
    'location', 'packages/db/sql/02_kg_schema.sql',
    'algorithm', 'recursive_cte'
  )
)
ON CONFLICT (slug) DO NOTHING;

-- ============================================================================
-- WORKFLOWS & DEPLOYMENTS
-- ============================================================================

INSERT INTO kg.nodes (slug, type, title, description, props, metadata) VALUES
(
  'workflow:ci-validation',
  'workflow',
  'CI/CD Validation Workflow',
  'GitHub Actions workflow for automated testing, linting, and deployment validation',
  jsonb_build_object(
    'platform', 'GitHub Actions',
    'triggers', jsonb_build_array('push', 'pull_request'),
    'steps', jsonb_build_array('lint', 'type-check', 'test', 'build')
  ),
  jsonb_build_object(
    'location', '.github/workflows/ci.yml',
    'timeout', '10m'
  )
),
(
  'deployment:vercel-prod',
  'deployment',
  'Vercel Production Deployment',
  'Production deployment of AI Workbench UI on Vercel edge network',
  jsonb_build_object(
    'platform', 'Vercel',
    'framework', 'Next.js 14',
    'environment', 'production'
  ),
  jsonb_build_object(
    'url', 'https://workbench.insightpulseai.net',
    'region', 'global-edge'
  )
)
ON CONFLICT (slug) DO NOTHING;

-- ============================================================================
-- AGENTS & SKILLS
-- ============================================================================

INSERT INTO kg.nodes (slug, type, title, description, props, metadata) VALUES
(
  'agent:research-agent',
  'agent',
  'Research & Documentation Agent',
  'Specialized agent for deep research, information synthesis, and documentation generation',
  jsonb_build_object(
    'capabilities', jsonb_build_array('web_search', 'document_analysis', 'synthesis'),
    'model', 'gpt-4-turbo'
  ),
  jsonb_build_object(
    'token_budget', '8K',
    'location', 'packages/agents/research/'
  )
),
(
  'skill:semantic-search',
  'skill',
  'Semantic Search Skill',
  'Skill for vector-based semantic search across knowledge graph nodes',
  jsonb_build_object(
    'type', 'vector_search',
    'function', 'kg.graph_search()',
    'min_similarity', 0.7
  ),
  jsonb_build_object(
    'agent_compatible', jsonb_build_array('research-agent', 'sql-generator')
  )
),
(
  'skill:graph-context',
  'skill',
  'Graph Context Gathering Skill',
  'Skill for gathering semantic + relational context for agent tasks',
  jsonb_build_object(
    'type', 'graph_query',
    'function', 'kg.graph_context_for()',
    'max_nodes', 20
  ),
  jsonb_build_object(
    'agent_compatible', jsonb_build_array('research-agent', 'code-reviewer')
  )
)
ON CONFLICT (slug) DO NOTHING;

-- ============================================================================
-- MIGRATIONS & SPEC KITS
-- ============================================================================

INSERT INTO kg.nodes (slug, type, title, description, props, metadata) VALUES
(
  'migration:02_kg_nodes_edges',
  'migration',
  'Knowledge Graph Schema Migration',
  'Complete DDL for kg schema with nodes, edges, functions, indexes, and RLS',
  jsonb_build_object(
    'version', '02',
    'file', 'packages/db/sql/02_kg_nodes_edges.sql',
    'tables', jsonb_build_array('nodes', 'edges', 'ingestion_log', 'schema_version')
  ),
  jsonb_build_object(
    'applied_at', '2025-12-09',
    'lines_of_code', 430
  )
),
(
  'migration:04_core_entities',
  'migration',
  'Core Entities Migration',
  'Operational entities for multi-tenant agent orchestration',
  jsonb_build_object(
    'version', '04',
    'file', 'packages/db/sql/04_core_entities.sql',
    'tables', jsonb_build_array('tenants', 'workspaces', 'agents', 'agent_runs', 'skills', 'agent_skills')
  ),
  jsonb_build_object(
    'applied_at', '2025-12-09',
    'lines_of_code', 350
  )
),
(
  'spec:data-model',
  'spec_kit',
  'Canonical Data Model Specification',
  'Complete reference for naming conventions, entity specs, RLS patterns, and migration strategy',
  jsonb_build_object(
    'file', 'docs/DATA_MODEL.md',
    'components', jsonb_build_array('naming_conventions', 'entity_specs', 'erd', 'rls_patterns')
  ),
  jsonb_build_object(
    'created_at', '2025-12-09',
    'status', 'canonical'
  )
)
ON CONFLICT (slug) DO NOTHING;

-- ============================================================================
-- EDGES: RELATIONSHIPS
-- ============================================================================

-- Repository relationships
INSERT INTO kg.edges (src_slug, dst_slug, type, weight) VALUES
('repo:archi-agent-framework', 'service:supabase-core', 'uses_service', 1.0),
('repo:archi-agent-framework', 'service:litellm-gateway', 'uses_service', 1.0),
('repo:archi-agent-framework', 'service:vercel-hosting', 'deployed_to', 1.0),
('repo:archi-agent-framework', 'database:knowledge-graph', 'stores_data_in', 1.0)
ON CONFLICT (src_slug, dst_slug, type) DO NOTHING;

-- Database schema relationships
INSERT INTO kg.edges (src_slug, dst_slug, type, weight) VALUES
('database:knowledge-graph', 'schema:kg', 'depends_on', 1.0),
('database:knowledge-graph', 'schema:public', 'depends_on', 1.0),
('database:knowledge-graph', 'schema:rag', 'depends_on', 1.0),
('schema:kg', 'migration:02_kg_nodes_edges', 'has_migration', 1.0),
('schema:public', 'migration:04_core_entities', 'has_migration', 1.0)
ON CONFLICT (src_slug, dst_slug, type) DO NOTHING;

-- Service dependencies
INSERT INTO kg.edges (src_slug, dst_slug, type, weight) VALUES
('service:supabase-core', 'database:knowledge-graph', 'stores_data_in', 1.0),
('service:vercel-hosting', 'service:supabase-core', 'uses_service', 1.0),
('service:vercel-hosting', 'deployment:vercel-prod', 'deployed_to', 1.0)
ON CONFLICT (src_slug, dst_slug, type) DO NOTHING;

-- Module relationships
INSERT INTO kg.edges (src_slug, dst_slug, type, weight) VALUES
('module:agent-layer', 'service:litellm-gateway', 'uses_service', 1.0),
('module:agent-layer', 'module:vector-search', 'depends_on', 1.0),
('module:agent-layer', 'module:graph-traversal', 'depends_on', 1.0),
('module:vector-search', 'schema:kg', 'stores_data_in', 1.0),
('module:graph-traversal', 'schema:kg', 'stores_data_in', 1.0)
ON CONFLICT (src_slug, dst_slug, type) DO NOTHING;

-- Workflow relationships
INSERT INTO kg.edges (src_slug, dst_slug, type, weight) VALUES
('workflow:ci-validation', 'repo:archi-agent-framework', 'validated_by', 1.0),
('workflow:ci-validation', 'deployment:vercel-prod', 'triggers_workflow', 1.0)
ON CONFLICT (src_slug, dst_slug, type) DO NOTHING;

-- Agent & skill relationships
INSERT INTO kg.edges (src_slug, dst_slug, type, weight) VALUES
('agent:research-agent', 'skill:semantic-search', 'uses_service', 1.0),
('agent:research-agent', 'skill:graph-context', 'uses_service', 1.0),
('skill:semantic-search', 'module:vector-search', 'implements_spec', 1.0),
('skill:graph-context', 'module:graph-traversal', 'implements_spec', 1.0),
('module:agent-layer', 'agent:research-agent', 'powers_agent', 1.0)
ON CONFLICT (src_slug, dst_slug, type) DO NOTHING;

-- Migration & spec relationships
INSERT INTO kg.edges (src_slug, dst_slug, type, weight) VALUES
('migration:02_kg_nodes_edges', 'spec:data-model', 'implements_spec', 1.0),
('migration:04_core_entities', 'spec:data-model', 'implements_spec', 1.0),
('schema:kg', 'spec:data-model', 'implements_spec', 1.0),
('schema:public', 'spec:data-model', 'implements_spec', 1.0),
('schema:rag', 'spec:data-model', 'implements_spec', 1.0)
ON CONFLICT (src_slug, dst_slug, type) DO NOTHING;

-- Seed data tracking
INSERT INTO kg.edges (src_slug, dst_slug, type, weight) VALUES
('schema:kg', 'repo:archi-agent-framework', 'has_seed_data', 1.0),
('database:knowledge-graph', 'repo:archi-agent-framework', 'has_seed_data', 1.0)
ON CONFLICT (src_slug, dst_slug, type) DO NOTHING;

-- RLS enforcement
INSERT INTO kg.edges (src_slug, dst_slug, type, weight) VALUES
('schema:public', 'service:supabase-core', 'enforces_rls', 1.0),
('schema:rag', 'service:supabase-core', 'enforces_rls', 1.0)
ON CONFLICT (src_slug, dst_slug, type) DO NOTHING;

COMMIT;

-- ============================================================================
-- Seed Verification
-- ============================================================================

-- Expected counts:
-- - Nodes: 18 (1 repo + 3 services + 4 databases/schemas + 3 modules + 2 workflows/deployments + 3 agents/skills + 3 migrations/specs)
-- - Edges: 33 (relationships across all node types)

-- Quick validation query:
-- SELECT type, COUNT(*) as count FROM kg.nodes GROUP BY type ORDER BY count DESC;
-- SELECT type, COUNT(*) as count FROM kg.edges GROUP BY type ORDER BY count DESC;
