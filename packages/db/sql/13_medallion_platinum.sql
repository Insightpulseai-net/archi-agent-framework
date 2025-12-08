-- ============================================================================
-- Platinum Layer: RAG Embeddings & AI-Ready Data
-- Purpose: Vector embeddings for semantic search and AI agent context
-- Pattern: Linked to Gold views with vector(1536) embeddings
-- ============================================================================

-- ============================================================================
-- Platinum Tables: Vector Embeddings
-- ============================================================================

-- Platinum Expense Embeddings: Semantic search for expense descriptions
CREATE TABLE IF NOT EXISTS scout.platinum_expense_embeddings (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID        NOT NULL,
  workspace_id      UUID,
  expense_id        UUID        NOT NULL REFERENCES scout.silver_expenses(id) ON DELETE CASCADE,

  -- Embedding fields
  embedding         vector(1536) NOT NULL,
  model             TEXT        NOT NULL DEFAULT 'text-embedding-3-small',
  text_content      TEXT        NOT NULL,

  -- Context fields
  category          TEXT,
  vendor_name       TEXT,
  amount            NUMERIC(15,2),
  expense_date      TIMESTAMPTZ,

  -- Metadata
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata          JSONB       NOT NULL DEFAULT '{}'::jsonb
);

-- Platinum BIR Form Embeddings: Semantic search for tax compliance documentation
CREATE TABLE IF NOT EXISTS scout.platinum_bir_embeddings (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID        NOT NULL,
  workspace_id      UUID,
  bir_form_id       UUID        NOT NULL REFERENCES scout.silver_bir_forms(id) ON DELETE CASCADE,

  -- Embedding fields
  embedding         vector(1536) NOT NULL,
  model             TEXT        NOT NULL DEFAULT 'text-embedding-3-small',
  text_content      TEXT        NOT NULL,

  -- Context fields
  form_type         TEXT        NOT NULL,
  filing_period     TEXT        NOT NULL,
  agency_name       TEXT,

  -- Metadata
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata          JSONB       NOT NULL DEFAULT '{}'::jsonb
);

-- Platinum PPM Task Embeddings: Semantic search for project task descriptions
CREATE TABLE IF NOT EXISTS scout.platinum_ppm_embeddings (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID        NOT NULL,
  workspace_id      UUID,
  ppm_task_id       UUID        NOT NULL REFERENCES scout.silver_ppm_tasks(id) ON DELETE CASCADE,

  -- Embedding fields
  embedding         vector(1536) NOT NULL,
  model             TEXT        NOT NULL DEFAULT 'text-embedding-3-small',
  text_content      TEXT        NOT NULL,

  -- Context fields
  task_type         TEXT        NOT NULL,
  logframe_level    TEXT,
  priority          TEXT,

  -- Metadata
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata          JSONB       NOT NULL DEFAULT '{}'::jsonb
);

-- Platinum Agency Knowledge: Semantic search for agency/client context
CREATE TABLE IF NOT EXISTS scout.platinum_agency_embeddings (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID        NOT NULL,
  workspace_id      UUID,
  agency_id         UUID        NOT NULL REFERENCES scout.silver_agencies(id) ON DELETE CASCADE,

  -- Embedding fields
  embedding         vector(1536) NOT NULL,
  model             TEXT        NOT NULL DEFAULT 'text-embedding-3-small',
  text_content      TEXT        NOT NULL,

  -- Context fields
  agency_code       TEXT        NOT NULL,
  agency_name       TEXT        NOT NULL,

  -- Metadata
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata          JSONB       NOT NULL DEFAULT '{}'::jsonb
);

-- Platinum Analytics Insights: Pre-generated insights from Gold views
CREATE TABLE IF NOT EXISTS scout.platinum_analytics_insights (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID        NOT NULL,
  workspace_id      UUID,

  -- Insight fields
  insight_type      TEXT        NOT NULL,
  insight_title     TEXT        NOT NULL,
  insight_text      TEXT        NOT NULL,
  source_view       TEXT        NOT NULL,

  -- Embedding fields
  embedding         vector(1536) NOT NULL,
  model             TEXT        NOT NULL DEFAULT 'text-embedding-3-small',

  -- Metadata
  generated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata          JSONB       NOT NULL DEFAULT '{}'::jsonb
);

-- ============================================================================
-- Indexes for Vector Search (IVFFlat)
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_platinum_expense_embeddings_vector
  ON scout.platinum_expense_embeddings
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_platinum_bir_embeddings_vector
  ON scout.platinum_bir_embeddings
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_platinum_ppm_embeddings_vector
  ON scout.platinum_ppm_embeddings
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_platinum_agency_embeddings_vector
  ON scout.platinum_agency_embeddings
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_platinum_analytics_insights_vector
  ON scout.platinum_analytics_insights
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- ============================================================================
-- Additional Indexes for Filtering
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_platinum_expense_embeddings_tenant_id
  ON scout.platinum_expense_embeddings(tenant_id);
CREATE INDEX IF NOT EXISTS idx_platinum_expense_embeddings_category
  ON scout.platinum_expense_embeddings(category);

CREATE INDEX IF NOT EXISTS idx_platinum_bir_embeddings_tenant_id
  ON scout.platinum_bir_embeddings(tenant_id);
CREATE INDEX IF NOT EXISTS idx_platinum_bir_embeddings_form_type
  ON scout.platinum_bir_embeddings(form_type);

CREATE INDEX IF NOT EXISTS idx_platinum_ppm_embeddings_tenant_id
  ON scout.platinum_ppm_embeddings(tenant_id);
CREATE INDEX IF NOT EXISTS idx_platinum_ppm_embeddings_task_type
  ON scout.platinum_ppm_embeddings(task_type);

CREATE INDEX IF NOT EXISTS idx_platinum_agency_embeddings_tenant_id
  ON scout.platinum_agency_embeddings(tenant_id);
CREATE INDEX IF NOT EXISTS idx_platinum_agency_embeddings_code
  ON scout.platinum_agency_embeddings(agency_code);

CREATE INDEX IF NOT EXISTS idx_platinum_analytics_insights_tenant_id
  ON scout.platinum_analytics_insights(tenant_id);
CREATE INDEX IF NOT EXISTS idx_platinum_analytics_insights_type
  ON scout.platinum_analytics_insights(insight_type);

-- ============================================================================
-- Row-Level Security (RLS) Policies
-- ============================================================================

ALTER TABLE scout.platinum_expense_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE scout.platinum_bir_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE scout.platinum_ppm_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE scout.platinum_agency_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE scout.platinum_analytics_insights ENABLE ROW LEVEL SECURITY;

CREATE POLICY platinum_expense_embeddings_tenant_isolation ON scout.platinum_expense_embeddings
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY platinum_bir_embeddings_tenant_isolation ON scout.platinum_bir_embeddings
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY platinum_ppm_embeddings_tenant_isolation ON scout.platinum_ppm_embeddings
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY platinum_agency_embeddings_tenant_isolation ON scout.platinum_agency_embeddings
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY platinum_analytics_insights_tenant_isolation ON scout.platinum_analytics_insights
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- ============================================================================
-- Functions for Semantic Search
-- ============================================================================

-- Semantic search for expenses
CREATE OR REPLACE FUNCTION scout.search_expenses_semantic(
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.8,
  match_count int DEFAULT 10,
  p_tenant_id uuid DEFAULT NULL
)
RETURNS TABLE (
  expense_id uuid,
  category text,
  vendor_name text,
  amount numeric,
  expense_date timestamptz,
  text_content text,
  similarity float
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    e.expense_id,
    e.category,
    e.vendor_name,
    e.amount,
    e.expense_date,
    e.text_content,
    1 - (e.embedding <=> query_embedding) AS similarity
  FROM scout.platinum_expense_embeddings e
  WHERE (p_tenant_id IS NULL OR e.tenant_id = p_tenant_id)
    AND 1 - (e.embedding <=> query_embedding) > match_threshold
  ORDER BY e.embedding <=> query_embedding
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Semantic search for BIR forms
CREATE OR REPLACE FUNCTION scout.search_bir_forms_semantic(
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.8,
  match_count int DEFAULT 10,
  p_tenant_id uuid DEFAULT NULL
)
RETURNS TABLE (
  bir_form_id uuid,
  form_type text,
  filing_period text,
  agency_name text,
  text_content text,
  similarity float
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    b.bir_form_id,
    b.form_type,
    b.filing_period,
    b.agency_name,
    b.text_content,
    1 - (b.embedding <=> query_embedding) AS similarity
  FROM scout.platinum_bir_embeddings b
  WHERE (p_tenant_id IS NULL OR b.tenant_id = p_tenant_id)
    AND 1 - (b.embedding <=> query_embedding) > match_threshold
  ORDER BY b.embedding <=> query_embedding
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Semantic search for PPM tasks
CREATE OR REPLACE FUNCTION scout.search_ppm_tasks_semantic(
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.8,
  match_count int DEFAULT 10,
  p_tenant_id uuid DEFAULT NULL
)
RETURNS TABLE (
  ppm_task_id uuid,
  task_type text,
  logframe_level text,
  priority text,
  text_content text,
  similarity float
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    p.ppm_task_id,
    p.task_type,
    p.logframe_level,
    p.priority,
    p.text_content,
    1 - (p.embedding <=> query_embedding) AS similarity
  FROM scout.platinum_ppm_embeddings p
  WHERE (p_tenant_id IS NULL OR p.tenant_id = p_tenant_id)
    AND 1 - (p.embedding <=> query_embedding) > match_threshold
  ORDER BY p.embedding <=> query_embedding
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Semantic search for analytics insights
CREATE OR REPLACE FUNCTION scout.search_analytics_insights_semantic(
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.8,
  match_count int DEFAULT 10,
  p_tenant_id uuid DEFAULT NULL
)
RETURNS TABLE (
  insight_id uuid,
  insight_type text,
  insight_title text,
  insight_text text,
  source_view text,
  similarity float
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    a.id,
    a.insight_type,
    a.insight_title,
    a.insight_text,
    a.source_view,
    1 - (a.embedding <=> query_embedding) AS similarity
  FROM scout.platinum_analytics_insights a
  WHERE (p_tenant_id IS NULL OR a.tenant_id = p_tenant_id)
    AND 1 - (a.embedding <=> query_embedding) > match_threshold
  ORDER BY a.embedding <=> query_embedding
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Triggers for Automatic Timestamps
-- ============================================================================

CREATE TRIGGER update_platinum_expense_embeddings_updated_at
  BEFORE UPDATE ON scout.platinum_expense_embeddings
  FOR EACH ROW EXECUTE FUNCTION scout.update_updated_at_column();

CREATE TRIGGER update_platinum_bir_embeddings_updated_at
  BEFORE UPDATE ON scout.platinum_bir_embeddings
  FOR EACH ROW EXECUTE FUNCTION scout.update_updated_at_column();

CREATE TRIGGER update_platinum_ppm_embeddings_updated_at
  BEFORE UPDATE ON scout.platinum_ppm_embeddings
  FOR EACH ROW EXECUTE FUNCTION scout.update_updated_at_column();

CREATE TRIGGER update_platinum_agency_embeddings_updated_at
  BEFORE UPDATE ON scout.platinum_agency_embeddings
  FOR EACH ROW EXECUTE FUNCTION scout.update_updated_at_column();

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE scout.platinum_expense_embeddings IS 'Vector embeddings for semantic expense search - text-embedding-3-small model';
COMMENT ON TABLE scout.platinum_bir_embeddings IS 'Vector embeddings for BIR form semantic search';
COMMENT ON TABLE scout.platinum_ppm_embeddings IS 'Vector embeddings for PPM task semantic search';
COMMENT ON TABLE scout.platinum_agency_embeddings IS 'Vector embeddings for agency context semantic search';
COMMENT ON TABLE scout.platinum_analytics_insights IS 'Pre-generated analytics insights with embeddings for natural language querying';

COMMENT ON FUNCTION scout.search_expenses_semantic IS 'Semantic search for expenses using cosine similarity - returns top K matches above threshold';
COMMENT ON FUNCTION scout.search_bir_forms_semantic IS 'Semantic search for BIR forms using cosine similarity';
COMMENT ON FUNCTION scout.search_ppm_tasks_semantic IS 'Semantic search for PPM tasks using cosine similarity';
COMMENT ON FUNCTION scout.search_analytics_insights_semantic IS 'Semantic search for analytics insights using natural language queries';

COMMENT ON INDEX idx_platinum_expense_embeddings_vector IS 'IVFFlat index for fast approximate nearest neighbor search (lists=100)';
