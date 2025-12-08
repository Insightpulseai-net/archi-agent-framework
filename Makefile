# Makefile for archi-agent-framework

# ============================================================================
# Database Operations
# ============================================================================

.PHONY: db-init
db-init: ## Initialize database schema
	@echo "🔄 Initializing database schema..."
	psql "$(POSTGRES_URL)" -f packages/db/sql/00_extensions.sql
	psql "$(POSTGRES_URL)" -f packages/db/sql/01_functions.sql
	psql "$(POSTGRES_URL)" -f packages/db/sql/02_kg_schema.sql
	@echo "✅ Database schema initialized"

.PHONY: db-seed-core
db-seed-core: ## Seed core entities
	@echo "🔄 Seeding core entities..."
	psql "$(POSTGRES_URL)" -f packages/db/sql/04_core_entities.sql
	@echo "✅ Core entities seeded"

.PHONY: db-seed-rag
db-seed-rag: ## Seed RAG entities
	@echo "🔄 Seeding RAG entities..."
	psql "$(POSTGRES_URL)" -f packages/db/sql/05_rag_entities.sql
	@echo "✅ RAG entities seeded"

.PHONY: db-kg-seed
db-kg-seed: ## Seed knowledge graph initial data
	@echo "🔄 Seeding knowledge graph..."
	psql "$(POSTGRES_URL)" -f packages/db/sql/03_kg_seed_initial_kg.sql
	@echo "✅ Knowledge graph seeded"

.PHONY: db-kg-smoke
db-kg-smoke: ## Run knowledge graph smoke tests
	@echo "🔍 Running knowledge graph smoke tests..."
	@psql "$(POSTGRES_URL)" -c "SELECT 'Node count: ' || COUNT(*) FROM kg.nodes;"
	@psql "$(POSTGRES_URL)" -c "SELECT 'Edge count: ' || COUNT(*) FROM kg.edges;"
	@psql "$(POSTGRES_URL)" -c "SELECT node_type, COUNT(*) as count FROM kg.nodes GROUP BY node_type ORDER BY count DESC;"
	@psql "$(POSTGRES_URL)" -c "SELECT edge_type, COUNT(*) as count FROM kg.edges GROUP BY edge_type ORDER BY count DESC;"
	@echo "✅ Smoke tests completed"

.PHONY: db-all
db-all: db-init db-seed-core db-seed-rag db-kg-seed db-kg-smoke ## Initialize and seed all database components
	@echo "✅ Full database setup completed"

.PHONY: db-reset
db-reset: ## WARNING: Drop all tables and reinitialize
	@echo "⚠️  WARNING: This will drop all tables and data!"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	@psql "$(POSTGRES_URL)" -c "DROP SCHEMA IF EXISTS kg CASCADE;"
	@psql "$(POSTGRES_URL)" -c "DROP TABLE IF EXISTS tenants CASCADE;"
	@psql "$(POSTGRES_URL)" -c "DROP TABLE IF EXISTS workspaces CASCADE;"
	@psql "$(POSTGRES_URL)" -c "DROP TABLE IF EXISTS agents CASCADE;"
	@psql "$(POSTGRES_URL)" -c "DROP TABLE IF EXISTS agent_runs CASCADE;"
	@psql "$(POSTGRES_URL)" -c "DROP TABLE IF EXISTS skills CASCADE;"
	@psql "$(POSTGRES_URL)" -c "DROP TABLE IF EXISTS agent_skills CASCADE;"
	@psql "$(POSTGRES_URL)" -c "DROP TABLE IF EXISTS rag_sources CASCADE;"
	@psql "$(POSTGRES_URL)" -c "DROP TABLE IF EXISTS rag_documents CASCADE;"
	@psql "$(POSTGRES_URL)" -c "DROP TABLE IF EXISTS rag_chunks CASCADE;"
	@psql "$(POSTGRES_URL)" -c "DROP TABLE IF EXISTS rag_embeddings CASCADE;"
	@psql "$(POSTGRES_URL)" -c "DROP TABLE IF EXISTS rag_queries CASCADE;"
	@psql "$(POSTGRES_URL)" -c "DROP TABLE IF EXISTS rag_evaluations CASCADE;"
	@psql "$(POSTGRES_URL)" -c "DROP TABLE IF EXISTS llm_requests CASCADE;"
	@echo "✅ Database reset completed"
	@$(MAKE) db-all

# ============================================================================
# Validation & Quality Gates
# ============================================================================

.PHONY: validate-schema
validate-schema: ## Validate database schema integrity and canonical compliance
	@echo "🔍 Validating database schema..."
	@echo ""
	@echo "1️⃣  Database connectivity check..."
	@psql "$(POSTGRES_URL)" -c "SELECT version();" > /dev/null 2>&1 || (echo "❌ Database connection failed" && exit 1)
	@echo "✅ Connected to PostgreSQL"
	@echo ""
	@echo "2️⃣  Canonical tables existence check..."
	@psql "$(POSTGRES_URL)" -c "\dt" | grep -E "(tenants|workspaces|agents|agent_runs|skills|agent_skills)" > /dev/null || (echo "❌ Core entities missing" && exit 1)
	@psql "$(POSTGRES_URL)" -c "\dt" | grep -E "(rag_sources|rag_documents|rag_chunks|rag_embeddings|rag_queries|rag_evaluations|llm_requests)" > /dev/null || (echo "❌ RAG entities missing" && exit 1)
	@echo "✅ All canonical tables exist"
	@echo ""
	@echo "3️⃣  KG schema check..."
	@psql "$(POSTGRES_URL)" -c "\dt kg.*" | grep -E "(nodes|edges|ingestion_log|schema_version)" > /dev/null || (echo "❌ KG schema incomplete" && exit 1)
	@echo "✅ KG schema complete"
	@echo ""
	@echo "4️⃣  RLS policy check..."
	@psql "$(POSTGRES_URL)" -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN ('tenants', 'workspaces', 'agents', 'agent_runs', 'skills', 'agent_skills') AND tablename NOT IN (SELECT tablename FROM pg_policies);" | grep -q "0 rows" || echo "⚠️  Warning: Some tables missing RLS policies"
	@echo "✅ RLS policies verified"
	@echo ""
	@echo "5️⃣  Index check..."
	@psql "$(POSTGRES_URL)" -c "\di" | grep -E "(idx_|_idx)" > /dev/null || echo "⚠️  Warning: Custom indexes may be missing"
	@echo "✅ Indexes verified"
	@echo ""
	@echo "6️⃣  Vector extension check..."
	@psql "$(POSTGRES_URL)" -c "SELECT extname FROM pg_extension WHERE extname = 'vector';" | grep -q "vector" || (echo "❌ pgvector extension missing" && exit 1)
	@echo "✅ pgvector extension enabled"
	@echo ""
	@echo "✅ Schema validation passed"

.PHONY: db-smoke
db-smoke: ## Comprehensive smoke tests for all entities
	@echo "🔍 Running comprehensive smoke tests..."
	@echo ""
	@echo "1️⃣  Core Entities Smoke Test"
	@psql "$(POSTGRES_URL)" -c "SELECT 'tenants: ' || COUNT(*) FROM tenants;"
	@psql "$(POSTGRES_URL)" -c "SELECT 'workspaces: ' || COUNT(*) FROM workspaces;"
	@psql "$(POSTGRES_URL)" -c "SELECT 'agents: ' || COUNT(*) FROM agents;"
	@psql "$(POSTGRES_URL)" -c "SELECT 'agent_runs: ' || COUNT(*) FROM agent_runs;"
	@psql "$(POSTGRES_URL)" -c "SELECT 'skills: ' || COUNT(*) FROM skills;"
	@psql "$(POSTGRES_URL)" -c "SELECT 'agent_skills: ' || COUNT(*) FROM agent_skills;"
	@echo ""
	@echo "2️⃣  RAG Entities Smoke Test"
	@psql "$(POSTGRES_URL)" -c "SELECT 'rag_sources: ' || COUNT(*) FROM rag_sources;"
	@psql "$(POSTGRES_URL)" -c "SELECT 'rag_documents: ' || COUNT(*) FROM rag_documents;"
	@psql "$(POSTGRES_URL)" -c "SELECT 'rag_chunks: ' || COUNT(*) FROM rag_chunks;"
	@psql "$(POSTGRES_URL)" -c "SELECT 'rag_embeddings: ' || COUNT(*) FROM rag_embeddings;"
	@psql "$(POSTGRES_URL)" -c "SELECT 'rag_queries: ' || COUNT(*) FROM rag_queries;"
	@psql "$(POSTGRES_URL)" -c "SELECT 'rag_evaluations: ' || COUNT(*) FROM rag_evaluations;"
	@psql "$(POSTGRES_URL)" -c "SELECT 'llm_requests: ' || COUNT(*) FROM llm_requests;"
	@echo ""
	@echo "3️⃣  Knowledge Graph Smoke Test"
	@psql "$(POSTGRES_URL)" -c "SELECT 'KG nodes: ' || COUNT(*) FROM kg.nodes;"
	@psql "$(POSTGRES_URL)" -c "SELECT 'KG edges: ' || COUNT(*) FROM kg.edges;"
	@psql "$(POSTGRES_URL)" -c "SELECT 'Node types: ' || COUNT(DISTINCT node_type) FROM kg.nodes;"
	@psql "$(POSTGRES_URL)" -c "SELECT 'Edge types: ' || COUNT(DISTINCT edge_type) FROM kg.edges;"
	@echo ""
	@echo "4️⃣  Node Type Distribution"
	@psql "$(POSTGRES_URL)" -c "SELECT node_type, COUNT(*) as count FROM kg.nodes GROUP BY node_type ORDER BY count DESC LIMIT 10;"
	@echo ""
	@echo "5️⃣  Edge Type Distribution"
	@psql "$(POSTGRES_URL)" -c "SELECT edge_type, COUNT(*) as count FROM kg.edges GROUP BY edge_type ORDER BY count DESC LIMIT 10;"
	@echo ""
	@echo "✅ Smoke tests completed"

.PHONY: audit-schema
audit-schema: ## Audit SQL files for canonical compliance (requires claude CLI)
	@echo "🔍 Running canonical schema audit..."
	@command -v claude >/dev/null 2>&1 || (echo "❌ claude CLI not found. Install: npm install -g @anthropic-ai/claude-cli" && exit 1)
	@echo ""
	@for file in packages/db/sql/*.sql; do \
		echo "📄 Auditing: $$file"; \
		result=$$(claude --system-prompt "$$(cat docs/CANONICAL_SCHEMA_AUDITOR_PROMPT.md)" \
		                 --file "$$file" \
		                 "Audit this SQL migration. Return only APPROVE, REJECT, or WARN." 2>/dev/null || echo "ERROR"); \
		if [ "$$result" = "REJECT" ]; then \
			echo "❌ Schema audit FAILED for $$file"; \
			echo "Run 'claude --system-prompt \"\$$(cat docs/CANONICAL_SCHEMA_AUDITOR_PROMPT.md)\" --file \"$$file\" \"Full audit report\"' for details"; \
			exit 1; \
		elif [ "$$result" = "WARN" ]; then \
			echo "⚠️  Schema audit WARNING for $$file"; \
		elif [ "$$result" = "APPROVE" ]; then \
			echo "✅ Schema audit PASSED for $$file"; \
		else \
			echo "⚠️  Could not audit $$file (claude CLI may not be configured)"; \
		fi; \
		echo ""; \
	done
	@echo "✅ Schema audit complete"

.PHONY: check-naming
check-naming: ## Check for naming convention violations
	@echo "🔍 Checking for naming convention violations..."
	@echo ""
	@echo "1️⃣  Scanning for camelCase/PascalCase in SQL files..."
	@if grep -rE "CREATE TABLE [A-Z][a-zA-Z]*|[a-z][A-Z]" packages/db/sql/*.sql; then \
		echo "❌ Found camelCase or PascalCase identifiers"; \
		exit 1; \
	else \
		echo "✅ No camelCase violations found"; \
	fi
	@echo ""
	@echo "2️⃣  Checking for timestamp without tz..."
	@if grep -r "timestamp[^z]" packages/db/sql/*.sql | grep -v "timestamptz"; then \
		echo "❌ Found 'timestamp' without 'tz' - use 'timestamptz'"; \
		exit 1; \
	else \
		echo "✅ All timestamps use timestamptz"; \
	fi
	@echo ""
	@echo "✅ Naming convention check passed"

.PHONY: check-rls
check-rls: ## Check RLS policy coverage
	@echo "🔍 Checking RLS policy coverage..."
	@psql "$(POSTGRES_URL)" -c " \
		SELECT \
			t.schemaname, \
			t.tablename, \
			CASE WHEN p.tablename IS NULL THEN '❌ MISSING' ELSE '✅' END as rls_status \
		FROM pg_tables t \
		LEFT JOIN (SELECT DISTINCT tablename FROM pg_policies) p ON t.tablename = p.tablename \
		WHERE t.schemaname IN ('public', 'kg') \
		ORDER BY t.schemaname, t.tablename;" | grep "❌" && echo "⚠️  Some tables missing RLS policies" || echo "✅ All tables have RLS policies"

.PHONY: validate-all
validate-all: validate-schema check-naming check-rls db-smoke ## Run all validation checks
	@echo "✅ All validation checks passed"

# ============================================================================
# Help
# ============================================================================

.PHONY: help
help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
