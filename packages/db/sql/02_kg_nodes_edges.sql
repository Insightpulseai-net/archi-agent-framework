-- ============================================================================
-- Knowledge Graph Schema: Nodes, Edges, Embeddings
-- ============================================================================
-- Purpose: Store canonical entities (nodes) and relationships (edges) with
--          vector embeddings for semantic search and agent context retrieval.
-- Dependencies: Requires pgvector extension and uuid-ossp
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Create kg schema
CREATE SCHEMA IF NOT EXISTS kg;

-- ============================================================================
-- Core Tables
-- ============================================================================

-- kg.nodes: Canonical entity storage
CREATE TABLE IF NOT EXISTS kg.nodes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  slug TEXT NOT NULL UNIQUE,
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  props JSONB DEFAULT '{}'::jsonb,
  metadata JSONB DEFAULT '{}'::jsonb,
  embedding vector(1536),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT slug_format CHECK (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  CONSTRAINT type_valid CHECK (type IN (
    'product', 'service', 'database', 'schema', 'table', 'workflow',
    'repository', 'spec_kit', 'module', 'dashboard', 'agent', 'skill',
    'worktree_branch', 'migration', 'deployment'
  ))
);

CREATE INDEX IF NOT EXISTS idx_nodes_type ON kg.nodes(type);
CREATE INDEX IF NOT EXISTS idx_nodes_slug ON kg.nodes(slug);
CREATE INDEX IF NOT EXISTS idx_nodes_embedding ON kg.nodes USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_nodes_props_gin ON kg.nodes USING gin(props);
CREATE INDEX IF NOT EXISTS idx_nodes_created_at ON kg.nodes(created_at DESC);

COMMENT ON TABLE kg.nodes IS 'Canonical entity nodes in knowledge graph with vector embeddings';
COMMENT ON COLUMN kg.nodes.slug IS 'Unique kebab-case identifier (e.g., supabase-core, agent-layer)';
COMMENT ON COLUMN kg.nodes.type IS 'Node type from canonical taxonomy (15 types)';
COMMENT ON COLUMN kg.nodes.embedding IS 'OpenAI text-embedding-3-small (1536 dimensions)';
COMMENT ON COLUMN kg.nodes.props IS 'Type-specific properties (flexible schema)';

-- kg.edges: Relationships between nodes
CREATE TABLE IF NOT EXISTS kg.edges (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  src_slug TEXT NOT NULL REFERENCES kg.nodes(slug) ON DELETE CASCADE,
  dst_slug TEXT NOT NULL REFERENCES kg.nodes(slug) ON DELETE CASCADE,
  type TEXT NOT NULL,
  props JSONB DEFAULT '{}'::jsonb,
  metadata JSONB DEFAULT '{}'::jsonb,
  weight FLOAT DEFAULT 1.0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT edge_unique UNIQUE (src_slug, dst_slug, type),
  CONSTRAINT no_self_loops CHECK (src_slug != dst_slug),
  CONSTRAINT type_valid CHECK (type IN (
    'uses_service', 'depends_on', 'stores_data_in', 'has_dashboard',
    'implements_spec', 'merged_from', 'deployed_to', 'triggers_workflow',
    'has_migration', 'powers_agent', 'has_seed_data', 'enforces_rls',
    'validated_by'
  ))
);

CREATE INDEX IF NOT EXISTS idx_edges_src ON kg.edges(src_slug);
CREATE INDEX IF NOT EXISTS idx_edges_dst ON kg.edges(dst_slug);
CREATE INDEX IF NOT EXISTS idx_edges_type ON kg.edges(type);
CREATE INDEX IF NOT EXISTS idx_edges_weight ON kg.edges(weight DESC);
CREATE INDEX IF NOT EXISTS idx_edges_props_gin ON kg.edges USING gin(props);

COMMENT ON TABLE kg.edges IS 'Directed relationships between nodes with optional weight';
COMMENT ON COLUMN kg.edges.type IS 'Relationship type from canonical taxonomy (13 types)';
COMMENT ON COLUMN kg.edges.weight IS 'Edge importance (1.0 = normal, >1.0 = stronger)';

-- kg.ingestion_log: Audit trail for graph updates
CREATE TABLE IF NOT EXISTS kg.ingestion_log (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source TEXT NOT NULL,
  operation TEXT NOT NULL,
  node_slug TEXT,
  edge_id UUID,
  payload JSONB,
  status TEXT DEFAULT 'success',
  error_message TEXT,
  ingested_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT operation_valid CHECK (operation IN ('node_upsert', 'edge_create', 'node_delete', 'edge_delete', 'bulk_sync'))
);

CREATE INDEX IF NOT EXISTS idx_ingestion_source ON kg.ingestion_log(source);
CREATE INDEX IF NOT EXISTS idx_ingestion_status ON kg.ingestion_log(status);
CREATE INDEX IF NOT EXISTS idx_ingestion_timestamp ON kg.ingestion_log(ingested_at DESC);

COMMENT ON TABLE kg.ingestion_log IS 'Audit trail for all knowledge graph mutations';

-- kg.schema_version: Migration tracking
CREATE TABLE IF NOT EXISTS kg.schema_version (
  version TEXT PRIMARY KEY,
  applied_at TIMESTAMPTZ DEFAULT NOW(),
  description TEXT
);

INSERT INTO kg.schema_version (version, description)
VALUES ('02_kg_nodes_edges', 'Initial knowledge graph schema with nodes, edges, embeddings')
ON CONFLICT (version) DO NOTHING;

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION kg.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER nodes_updated_at BEFORE UPDATE ON kg.nodes
  FOR EACH ROW EXECUTE FUNCTION kg.update_updated_at();

CREATE TRIGGER edges_updated_at BEFORE UPDATE ON kg.edges
  FOR EACH ROW EXECUTE FUNCTION kg.update_updated_at();

-- Generate embedding from text (stub - requires Edge Function integration)
CREATE OR REPLACE FUNCTION kg.generate_embedding(text_input TEXT)
RETURNS vector(1536) AS $$
BEGIN
  -- Placeholder: Call Supabase Edge Function for OpenAI embeddings
  -- For now, return null vector (will be replaced with actual embedding)
  RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION kg.generate_embedding IS 'Generate OpenAI embedding via Edge Function (stub)';

-- Auto-embed node on insert/update
CREATE OR REPLACE FUNCTION kg.auto_embed_node()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.embedding IS NULL THEN
    NEW.embedding := kg.generate_embedding(
      NEW.title || ' ' || COALESCE(NEW.description, '')
    );
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER nodes_auto_embed BEFORE INSERT OR UPDATE ON kg.nodes
  FOR EACH ROW EXECUTE FUNCTION kg.auto_embed_node();

-- ============================================================================
-- Graph Query Functions
-- ============================================================================

-- 1. Semantic Search: Find nodes by natural language query
CREATE OR REPLACE FUNCTION kg.graph_search(
  query_text TEXT,
  node_type TEXT DEFAULT NULL,
  limit_results INT DEFAULT 10
)
RETURNS TABLE (
  slug TEXT,
  type TEXT,
  title TEXT,
  description TEXT,
  similarity FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    n.slug,
    n.type,
    n.title,
    n.description,
    1 - (n.embedding <=> kg.generate_embedding(query_text)) AS similarity
  FROM kg.nodes n
  WHERE (node_type IS NULL OR n.type = node_type)
    AND n.embedding IS NOT NULL
  ORDER BY n.embedding <=> kg.generate_embedding(query_text)
  LIMIT limit_results;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION kg.graph_search IS 'Semantic search using vector embeddings';

-- 2. Graph Neighbors: Traverse relationships from a node
CREATE OR REPLACE FUNCTION kg.graph_neighbors(
  node_slug TEXT,
  filter_edge_type TEXT DEFAULT NULL,
  direction TEXT DEFAULT 'outgoing',
  depth INT DEFAULT 1
)
RETURNS TABLE (
  slug TEXT,
  type TEXT,
  title TEXT,
  edge_type TEXT,
  hop_distance INT
) AS $$
BEGIN
  RETURN QUERY
  WITH RECURSIVE graph_walk AS (
    -- Base case: Direct neighbors
    SELECT
      CASE
        WHEN direction = 'outgoing' THEN e.dst_slug
        WHEN direction = 'incoming' THEN e.src_slug
        ELSE e.dst_slug  -- Default to outgoing
      END AS slug,
      n.type,
      n.title,
      e.type AS edge_type,
      1 AS hop_distance
    FROM kg.edges e
    JOIN kg.nodes n ON (
      CASE
        WHEN direction = 'outgoing' THEN n.slug = e.dst_slug
        WHEN direction = 'incoming' THEN n.slug = e.src_slug
        ELSE n.slug = e.dst_slug
      END
    )
    WHERE (
      CASE
        WHEN direction = 'outgoing' THEN e.src_slug = node_slug
        WHEN direction = 'incoming' THEN e.dst_slug = node_slug
        ELSE e.src_slug = node_slug
      END
    )
    AND (filter_edge_type IS NULL OR e.type = filter_edge_type)

    UNION ALL

    -- Recursive case: Walk further
    SELECT
      CASE
        WHEN direction = 'outgoing' THEN e.dst_slug
        WHEN direction = 'incoming' THEN e.src_slug
        ELSE e.dst_slug
      END AS slug,
      n.type,
      n.title,
      e.type AS edge_type,
      gw.hop_distance + 1 AS hop_distance
    FROM graph_walk gw
    JOIN kg.edges e ON (
      CASE
        WHEN direction = 'outgoing' THEN e.src_slug = gw.slug
        WHEN direction = 'incoming' THEN e.dst_slug = gw.slug
        ELSE e.src_slug = gw.slug
      END
    )
    JOIN kg.nodes n ON (
      CASE
        WHEN direction = 'outgoing' THEN n.slug = e.dst_slug
        WHEN direction = 'incoming' THEN n.slug = e.src_slug
        ELSE n.slug = e.dst_slug
      END
    )
    WHERE gw.hop_distance < depth
      AND (filter_edge_type IS NULL OR e.type = filter_edge_type)
  )
  SELECT DISTINCT ON (slug) * FROM graph_walk
  ORDER BY slug, hop_distance;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION kg.graph_neighbors IS 'Traverse graph relationships with configurable depth';

-- 3. Graph Path: Find shortest path between two nodes
CREATE OR REPLACE FUNCTION kg.graph_path(
  src_slug TEXT,
  dst_slug TEXT,
  max_depth INT DEFAULT 5
)
RETURNS TABLE (
  path_nodes TEXT[],
  path_edges TEXT[],
  path_length INT
) AS $$
BEGIN
  RETURN QUERY
  WITH RECURSIVE path_search AS (
    -- Base case: Start from source
    SELECT
      ARRAY[src_slug] AS nodes,
      ARRAY[]::TEXT[] AS edges,
      0 AS depth,
      src_slug AS current_node
    WHERE EXISTS (SELECT 1 FROM kg.nodes WHERE slug = src_slug)

    UNION ALL

    -- Recursive case: Extend path
    SELECT
      ps.nodes || e.dst_slug,
      ps.edges || e.type,
      ps.depth + 1,
      e.dst_slug
    FROM path_search ps
    JOIN kg.edges e ON e.src_slug = ps.current_node
    WHERE ps.depth < max_depth
      AND NOT (e.dst_slug = ANY(ps.nodes))  -- Prevent cycles
  )
  SELECT nodes, edges, depth
  FROM path_search
  WHERE current_node = dst_slug
  ORDER BY depth
  LIMIT 1;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION kg.graph_path IS 'Find shortest path between two nodes';

-- 4. Graph Context: Gather relevant context for a task
CREATE OR REPLACE FUNCTION kg.graph_context_for(
  task_description TEXT,
  max_nodes INT DEFAULT 20
)
RETURNS TABLE (
  slug TEXT,
  type TEXT,
  title TEXT,
  description TEXT,
  relevance_score FLOAT,
  connected_nodes JSONB
) AS $$
BEGIN
  RETURN QUERY
  WITH semantic_matches AS (
    -- Step 1: Semantic search for relevant nodes
    SELECT
      n.slug,
      n.type,
      n.title,
      n.description,
      1 - (n.embedding <=> kg.generate_embedding(task_description)) AS similarity
    FROM kg.nodes n
    WHERE n.embedding IS NOT NULL
    ORDER BY n.embedding <=> kg.generate_embedding(task_description)
    LIMIT max_nodes
  ),
  expanded_context AS (
    -- Step 2: Expand to immediate neighbors
    SELECT DISTINCT
      sm.slug,
      sm.type,
      sm.title,
      sm.description,
      sm.similarity AS relevance_score,
      jsonb_agg(
        jsonb_build_object(
          'slug', neighbor.slug,
          'type', neighbor.type,
          'title', neighbor.title,
          'edge_type', e.type
        )
      ) AS connected_nodes
    FROM semantic_matches sm
    LEFT JOIN kg.edges e ON e.src_slug = sm.slug OR e.dst_slug = sm.slug
    LEFT JOIN kg.nodes neighbor ON neighbor.slug = CASE
      WHEN e.src_slug = sm.slug THEN e.dst_slug
      ELSE e.src_slug
    END
    GROUP BY sm.slug, sm.type, sm.title, sm.description, sm.similarity
  )
  SELECT * FROM expanded_context
  ORDER BY relevance_score DESC;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION kg.graph_context_for IS 'Gather semantic + relational context for agent tasks';

-- ============================================================================
-- Row-Level Security (RLS)
-- ============================================================================

ALTER TABLE kg.nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE kg.edges ENABLE ROW LEVEL SECURITY;
ALTER TABLE kg.ingestion_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE kg.schema_version ENABLE ROW LEVEL SECURITY;

-- Public read access for all KG tables
CREATE POLICY "kg_nodes_read" ON kg.nodes FOR SELECT USING (true);
CREATE POLICY "kg_edges_read" ON kg.edges FOR SELECT USING (true);
CREATE POLICY "kg_ingestion_log_read" ON kg.ingestion_log FOR SELECT USING (true);
CREATE POLICY "kg_schema_version_read" ON kg.schema_version FOR SELECT USING (true);

-- Service role write access (for automation)
CREATE POLICY "kg_nodes_write" ON kg.nodes FOR ALL
  USING (auth.role() = 'service_role');
CREATE POLICY "kg_edges_write" ON kg.edges FOR ALL
  USING (auth.role() = 'service_role');
CREATE POLICY "kg_ingestion_log_write" ON kg.ingestion_log FOR ALL
  USING (auth.role() = 'service_role');

-- ============================================================================
-- Grant Permissions
-- ============================================================================

GRANT USAGE ON SCHEMA kg TO anon, authenticated, service_role;
GRANT SELECT ON ALL TABLES IN SCHEMA kg TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA kg TO service_role;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA kg TO anon, authenticated, service_role;

-- ============================================================================
-- Validation Queries
-- ============================================================================

-- Verify schema creation
DO $$
BEGIN
  ASSERT (SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'kg' AND tablename = 'nodes') = 1,
    'kg.nodes table not created';
  ASSERT (SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'kg' AND tablename = 'edges') = 1,
    'kg.edges table not created';
  RAISE NOTICE 'Knowledge Graph schema validation: PASSED';
END $$;
