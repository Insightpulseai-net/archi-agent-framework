-- 05_rag_entities.sql - RAG (Retrieval-Augmented Generation) entities

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- RAG Sources: External data sources for ingestion
-- ============================================================================

DROP TABLE IF EXISTS rag_sources CASCADE;

CREATE TABLE rag_sources (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  name text NOT NULL,
  slug text NOT NULL,
  source_type text NOT NULL CHECK (source_type IN ('github', 'notion', 'confluence', 'web', 'file', 'api')),
  connection_config jsonb DEFAULT '{}',
  sync_frequency text,
  last_synced_at timestamptz,
  status text DEFAULT 'active' CHECK (status IN ('active', 'paused', 'error')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT unique_rag_source_slug_per_workspace UNIQUE (workspace_id, slug)
);

-- Enable RLS
ALTER TABLE rag_sources ENABLE ROW LEVEL SECURITY;

-- Create updated_at trigger
CREATE TRIGGER update_rag_sources_updated_at
  BEFORE UPDATE ON rag_sources
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- Create indexes
CREATE INDEX idx_rag_sources_tenant_id ON rag_sources(tenant_id);
CREATE INDEX idx_rag_sources_workspace_id ON rag_sources(workspace_id);
CREATE INDEX idx_rag_sources_slug ON rag_sources(workspace_id, slug);
CREATE INDEX idx_rag_sources_source_type ON rag_sources(source_type);
CREATE INDEX idx_rag_sources_status ON rag_sources(status);

-- RLS Policy: Users can only see RAG sources within their tenant and workspace
CREATE POLICY rag_source_isolation ON rag_sources
  FOR ALL
  USING (
    tenant_id = current_setting('app.current_tenant_id', true)::uuid
    AND workspace_id = current_setting('app.current_workspace_id', true)::uuid
  );

-- ============================================================================
-- RAG Documents: Individual documents from sources
-- ============================================================================

DROP TABLE IF EXISTS rag_documents CASCADE;

CREATE TABLE rag_documents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  rag_source_id uuid NOT NULL REFERENCES rag_sources(id) ON DELETE CASCADE,
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  external_id text,
  title text NOT NULL,
  content_type text,
  url text,
  metadata jsonb DEFAULT '{}',
  content_hash text,
  indexed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT unique_rag_document_external_id UNIQUE (rag_source_id, external_id)
);

-- Enable RLS
ALTER TABLE rag_documents ENABLE ROW LEVEL SECURITY;

-- Create updated_at trigger
CREATE TRIGGER update_rag_documents_updated_at
  BEFORE UPDATE ON rag_documents
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- Create indexes
CREATE INDEX idx_rag_documents_rag_source_id ON rag_documents(rag_source_id);
CREATE INDEX idx_rag_documents_tenant_id ON rag_documents(tenant_id);
CREATE INDEX idx_rag_documents_workspace_id ON rag_documents(workspace_id);
CREATE INDEX idx_rag_documents_external_id ON rag_documents(rag_source_id, external_id);
CREATE INDEX idx_rag_documents_content_hash ON rag_documents(content_hash);
CREATE INDEX idx_rag_documents_indexed_at ON rag_documents(indexed_at DESC);

-- RLS Policy: Users can only see RAG documents within their tenant and workspace
CREATE POLICY rag_document_isolation ON rag_documents
  FOR ALL
  USING (
    tenant_id = current_setting('app.current_tenant_id', true)::uuid
    AND workspace_id = current_setting('app.current_workspace_id', true)::uuid
  );

-- ============================================================================
-- RAG Chunks: Semantic chunks of documents for retrieval
-- ============================================================================

DROP TABLE IF EXISTS rag_chunks CASCADE;

CREATE TABLE rag_chunks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  rag_document_id uuid NOT NULL REFERENCES rag_documents(id) ON DELETE CASCADE,
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  chunk_index integer NOT NULL,
  content text NOT NULL,
  token_count integer,
  metadata jsonb DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT unique_rag_chunk_per_document UNIQUE (rag_document_id, chunk_index)
);

-- Enable RLS
ALTER TABLE rag_chunks ENABLE ROW LEVEL SECURITY;

-- Create updated_at trigger
CREATE TRIGGER update_rag_chunks_updated_at
  BEFORE UPDATE ON rag_chunks
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- Create indexes
CREATE INDEX idx_rag_chunks_rag_document_id ON rag_chunks(rag_document_id);
CREATE INDEX idx_rag_chunks_tenant_id ON rag_chunks(tenant_id);
CREATE INDEX idx_rag_chunks_workspace_id ON rag_chunks(workspace_id);
CREATE INDEX idx_rag_chunks_chunk_index ON rag_chunks(rag_document_id, chunk_index);

-- RLS Policy: Users can only see RAG chunks within their tenant and workspace
CREATE POLICY rag_chunk_isolation ON rag_chunks
  FOR ALL
  USING (
    tenant_id = current_setting('app.current_tenant_id', true)::uuid
    AND workspace_id = current_setting('app.current_workspace_id', true)::uuid
  );

-- ============================================================================
-- RAG Embeddings: Vector embeddings for semantic search
-- ============================================================================

DROP TABLE IF EXISTS rag_embeddings CASCADE;

CREATE TABLE rag_embeddings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  rag_chunk_id uuid NOT NULL REFERENCES rag_chunks(id) ON DELETE CASCADE,
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  embedding_model text NOT NULL,
  embedding vector(1536),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT unique_rag_embedding_per_chunk_model UNIQUE (rag_chunk_id, embedding_model)
);

-- Enable RLS
ALTER TABLE rag_embeddings ENABLE ROW LEVEL SECURITY;

-- Create updated_at trigger
CREATE TRIGGER update_rag_embeddings_updated_at
  BEFORE UPDATE ON rag_embeddings
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- Create indexes
CREATE INDEX idx_rag_embeddings_rag_chunk_id ON rag_embeddings(rag_chunk_id);
CREATE INDEX idx_rag_embeddings_tenant_id ON rag_embeddings(tenant_id);
CREATE INDEX idx_rag_embeddings_workspace_id ON rag_embeddings(workspace_id);
CREATE INDEX idx_rag_embeddings_embedding_model ON rag_embeddings(embedding_model);

-- RLS Policy: Users can only see RAG embeddings within their tenant and workspace
CREATE POLICY rag_embedding_isolation ON rag_embeddings
  FOR ALL
  USING (
    tenant_id = current_setting('app.current_tenant_id', true)::uuid
    AND workspace_id = current_setting('app.current_workspace_id', true)::uuid
  );

-- ============================================================================
-- RAG Queries: User queries for retrieval tracking
-- ============================================================================

DROP TABLE IF EXISTS rag_queries CASCADE;

CREATE TABLE rag_queries (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  agent_run_id uuid REFERENCES agent_runs(id) ON DELETE SET NULL,
  query_text text NOT NULL,
  query_embedding vector(1536),
  query_metadata jsonb DEFAULT '{}',
  top_k integer DEFAULT 5,
  min_similarity real DEFAULT 0.7,
  retrieved_chunk_ids uuid[],
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE rag_queries ENABLE ROW LEVEL SECURITY;

-- Create indexes
CREATE INDEX idx_rag_queries_tenant_id ON rag_queries(tenant_id);
CREATE INDEX idx_rag_queries_workspace_id ON rag_queries(workspace_id);
CREATE INDEX idx_rag_queries_agent_run_id ON rag_queries(agent_run_id);
CREATE INDEX idx_rag_queries_created_at ON rag_queries(created_at DESC);

-- RLS Policy: Users can only see RAG queries within their tenant and workspace
CREATE POLICY rag_query_isolation ON rag_queries
  FOR ALL
  USING (
    tenant_id = current_setting('app.current_tenant_id', true)::uuid
    AND workspace_id = current_setting('app.current_workspace_id', true)::uuid
  );

-- ============================================================================
-- RAG Evaluations: Quality metrics for retrieval results
-- ============================================================================

DROP TABLE IF EXISTS rag_evaluations CASCADE;

CREATE TABLE rag_evaluations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  rag_query_id uuid NOT NULL REFERENCES rag_queries(id) ON DELETE CASCADE,
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  relevance_score real,
  precision_at_k real,
  recall_at_k real,
  mrr real,
  ndcg real,
  evaluation_metadata jsonb DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE rag_evaluations ENABLE ROW LEVEL SECURITY;

-- Create indexes
CREATE INDEX idx_rag_evaluations_rag_query_id ON rag_evaluations(rag_query_id);
CREATE INDEX idx_rag_evaluations_tenant_id ON rag_evaluations(tenant_id);
CREATE INDEX idx_rag_evaluations_workspace_id ON rag_evaluations(workspace_id);
CREATE INDEX idx_rag_evaluations_created_at ON rag_evaluations(created_at DESC);

-- RLS Policy: Users can only see RAG evaluations within their tenant and workspace
CREATE POLICY rag_evaluation_isolation ON rag_evaluations
  FOR ALL
  USING (
    tenant_id = current_setting('app.current_tenant_id', true)::uuid
    AND workspace_id = current_setting('app.current_workspace_id', true)::uuid
  );

-- ============================================================================
-- LLM Requests: Audit trail for LLM API calls
-- ============================================================================

DROP TABLE IF EXISTS llm_requests CASCADE;

CREATE TABLE llm_requests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  agent_run_id uuid REFERENCES agent_runs(id) ON DELETE SET NULL,
  rag_query_id uuid REFERENCES rag_queries(id) ON DELETE SET NULL,
  model text NOT NULL,
  provider text NOT NULL,
  prompt_tokens integer,
  completion_tokens integer,
  total_tokens integer,
  latency_ms integer,
  cost_usd numeric(10, 6),
  status text DEFAULT 'success' CHECK (status IN ('success', 'error', 'timeout')),
  error_message text,
  request_metadata jsonb DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE llm_requests ENABLE ROW LEVEL SECURITY;

-- Create indexes
CREATE INDEX idx_llm_requests_tenant_id ON llm_requests(tenant_id);
CREATE INDEX idx_llm_requests_workspace_id ON llm_requests(workspace_id);
CREATE INDEX idx_llm_requests_agent_run_id ON llm_requests(agent_run_id);
CREATE INDEX idx_llm_requests_rag_query_id ON llm_requests(rag_query_id);
CREATE INDEX idx_llm_requests_model ON llm_requests(model);
CREATE INDEX idx_llm_requests_provider ON llm_requests(provider);
CREATE INDEX idx_llm_requests_status ON llm_requests(status);
CREATE INDEX idx_llm_requests_created_at ON llm_requests(created_at DESC);

-- RLS Policy: Users can only see LLM requests within their tenant and workspace
CREATE POLICY llm_request_isolation ON llm_requests
  FOR ALL
  USING (
    tenant_id = current_setting('app.current_tenant_id', true)::uuid
    AND workspace_id = current_setting('app.current_workspace_id', true)::uuid
  );

-- ============================================================================
-- Verification
-- ============================================================================

DO $
BEGIN
  RAISE NOTICE '✅ RAG Entities Schema Created';
  RAISE NOTICE 'Tables:';
  RAISE NOTICE '  - rag_sources (% rows)', (SELECT COUNT(*) FROM rag_sources);
  RAISE NOTICE '  - rag_documents (% rows)', (SELECT COUNT(*) FROM rag_documents);
  RAISE NOTICE '  - rag_chunks (% rows)', (SELECT COUNT(*) FROM rag_chunks);
  RAISE NOTICE '  - rag_embeddings (% rows)', (SELECT COUNT(*) FROM rag_embeddings);
  RAISE NOTICE '  - rag_queries (% rows)', (SELECT COUNT(*) FROM rag_queries);
  RAISE NOTICE '  - rag_evaluations (% rows)', (SELECT COUNT(*) FROM rag_evaluations);
  RAISE NOTICE '  - llm_requests (% rows)', (SELECT COUNT(*) FROM llm_requests);
  RAISE NOTICE 'RLS Policies:';
  RAISE NOTICE '  - rag_source_isolation on rag_sources';
  RAISE NOTICE '  - rag_document_isolation on rag_documents';
  RAISE NOTICE '  - rag_chunk_isolation on rag_chunks';
  RAISE NOTICE '  - rag_embedding_isolation on rag_embeddings';
  RAISE NOTICE '  - rag_query_isolation on rag_queries';
  RAISE NOTICE '  - rag_evaluation_isolation on rag_evaluations';
  RAISE NOTICE '  - llm_request_isolation on llm_requests';
END;
$;
