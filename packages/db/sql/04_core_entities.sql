-- 04_core_entities.sql - Core data model entities (tenants, workspaces, agents, agent_runs, skills, agent_skills)

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Tenants: Top-level organization/account isolation
-- ============================================================================

DROP TABLE IF EXISTS tenants CASCADE;

CREATE TABLE tenants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  slug text UNIQUE NOT NULL,
  settings jsonb DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;

-- Create updated_at trigger
CREATE TRIGGER update_tenants_updated_at
  BEFORE UPDATE ON tenants
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- Create indexes
CREATE INDEX idx_tenants_slug ON tenants(slug);

-- RLS Policy: Users can only see their own tenant
CREATE POLICY tenant_isolation ON tenants
  FOR ALL
  USING (id = current_setting('app.current_tenant_id', true)::uuid);

-- ============================================================================
-- Workspaces: Sub-organization grouping (projects, teams, environments)
-- ============================================================================

DROP TABLE IF EXISTS workspaces CASCADE;

CREATE TABLE workspaces (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  name text NOT NULL,
  slug text NOT NULL,
  settings jsonb DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT unique_workspace_slug_per_tenant UNIQUE (tenant_id, slug)
);

-- Enable RLS
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;

-- Create updated_at trigger
CREATE TRIGGER update_workspaces_updated_at
  BEFORE UPDATE ON workspaces
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- Create indexes
CREATE INDEX idx_workspaces_tenant_id ON workspaces(tenant_id);
CREATE INDEX idx_workspaces_slug ON workspaces(tenant_id, slug);

-- RLS Policy: Users can only see workspaces within their tenant
CREATE POLICY workspace_isolation ON workspaces
  FOR ALL
  USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- ============================================================================
-- Agents: Registered AI agents/personas
-- ============================================================================

DROP TABLE IF EXISTS agents CASCADE;

CREATE TABLE agents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  name text NOT NULL,
  slug text NOT NULL,
  description text,
  agent_type text NOT NULL,
  config jsonb DEFAULT '{}',
  status text DEFAULT 'active' CHECK (status IN ('active', 'paused', 'archived')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT unique_agent_slug_per_workspace UNIQUE (workspace_id, slug)
);

-- Enable RLS
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;

-- Create updated_at trigger
CREATE TRIGGER update_agents_updated_at
  BEFORE UPDATE ON agents
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- Create indexes
CREATE INDEX idx_agents_tenant_id ON agents(tenant_id);
CREATE INDEX idx_agents_workspace_id ON agents(workspace_id);
CREATE INDEX idx_agents_slug ON agents(workspace_id, slug);
CREATE INDEX idx_agents_status ON agents(status);

-- RLS Policy: Users can only see agents within their tenant and workspace
CREATE POLICY agent_isolation ON agents
  FOR ALL
  USING (
    tenant_id = current_setting('app.current_tenant_id', true)::uuid
    AND workspace_id = current_setting('app.current_workspace_id', true)::uuid
  );

-- ============================================================================
-- Agent Runs: Individual agent execution logs
-- ============================================================================

DROP TABLE IF EXISTS agent_runs CASCADE;

CREATE TABLE agent_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id uuid NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  status text DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
  trigger text,
  input_params jsonb DEFAULT '{}',
  results jsonb DEFAULT '{}',
  error_message text,
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE agent_runs ENABLE ROW LEVEL SECURITY;

-- Create updated_at trigger
CREATE TRIGGER update_agent_runs_updated_at
  BEFORE UPDATE ON agent_runs
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- Create indexes
CREATE INDEX idx_agent_runs_agent_id ON agent_runs(agent_id, created_at DESC);
CREATE INDEX idx_agent_runs_tenant_id ON agent_runs(tenant_id);
CREATE INDEX idx_agent_runs_workspace_id ON agent_runs(workspace_id);
CREATE INDEX idx_agent_runs_status ON agent_runs(status, started_at);

-- RLS Policy: Users can only see agent runs within their tenant and workspace
CREATE POLICY agent_run_isolation ON agent_runs
  FOR ALL
  USING (
    tenant_id = current_setting('app.current_tenant_id', true)::uuid
    AND workspace_id = current_setting('app.current_workspace_id', true)::uuid
  );

-- ============================================================================
-- Skills: Atomic capabilities/functions
-- ============================================================================

DROP TABLE IF EXISTS skills CASCADE;

CREATE TABLE skills (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  name text NOT NULL,
  slug text UNIQUE NOT NULL,
  description text,
  skill_type text NOT NULL,
  implementation text,
  config jsonb DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE skills ENABLE ROW LEVEL SECURITY;

-- Create updated_at trigger
CREATE TRIGGER update_skills_updated_at
  BEFORE UPDATE ON skills
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- Create indexes
CREATE INDEX idx_skills_tenant_id ON skills(tenant_id);
CREATE INDEX idx_skills_slug ON skills(slug);
CREATE INDEX idx_skills_skill_type ON skills(skill_type);

-- RLS Policy: Users can only see skills within their tenant
CREATE POLICY skill_isolation ON skills
  FOR ALL
  USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- ============================================================================
-- Agent Skills: Many-to-many relationship between agents and skills
-- ============================================================================

DROP TABLE IF EXISTS agent_skills CASCADE;

CREATE TABLE agent_skills (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id uuid NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  skill_id uuid NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  is_required boolean DEFAULT false,
  config_override jsonb DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT unique_agent_skill UNIQUE (agent_id, skill_id)
);

-- Enable RLS
ALTER TABLE agent_skills ENABLE ROW LEVEL SECURITY;

-- Create indexes
CREATE INDEX idx_agent_skills_agent_id ON agent_skills(agent_id);
CREATE INDEX idx_agent_skills_skill_id ON agent_skills(skill_id);
CREATE INDEX idx_agent_skills_tenant_id ON agent_skills(tenant_id);

-- RLS Policy: Users can only see agent-skill relationships within their tenant
CREATE POLICY agent_skill_isolation ON agent_skills
  FOR ALL
  USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- ============================================================================
-- Helper Function: Set tenant and workspace context
-- ============================================================================

CREATE OR REPLACE FUNCTION set_tenant_context(tenant_uuid uuid, workspace_uuid uuid)
RETURNS void AS $
BEGIN
  PERFORM set_config('app.current_tenant_id', tenant_uuid::text, true);
  PERFORM set_config('app.current_workspace_id', workspace_uuid::text, true);
END;
$ LANGUAGE plpgsql;

-- ============================================================================
-- Verification
-- ============================================================================

DO $
BEGIN
  RAISE NOTICE '✅ Core Entities Schema Created';
  RAISE NOTICE 'Tables:';
  RAISE NOTICE '  - tenants (% rows)', (SELECT COUNT(*) FROM tenants);
  RAISE NOTICE '  - workspaces (% rows)', (SELECT COUNT(*) FROM workspaces);
  RAISE NOTICE '  - agents (% rows)', (SELECT COUNT(*) FROM agents);
  RAISE NOTICE '  - agent_runs (% rows)', (SELECT COUNT(*) FROM agent_runs);
  RAISE NOTICE '  - skills (% rows)', (SELECT COUNT(*) FROM skills);
  RAISE NOTICE '  - agent_skills (% rows)', (SELECT COUNT(*) FROM agent_skills);
  RAISE NOTICE 'RLS Policies:';
  RAISE NOTICE '  - tenant_isolation on tenants';
  RAISE NOTICE '  - workspace_isolation on workspaces';
  RAISE NOTICE '  - agent_isolation on agents';
  RAISE NOTICE '  - agent_run_isolation on agent_runs';
  RAISE NOTICE '  - skill_isolation on skills';
  RAISE NOTICE '  - agent_skill_isolation on agent_skills';
END;
$;
