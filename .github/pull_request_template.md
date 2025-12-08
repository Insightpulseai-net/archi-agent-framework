# Pull Request

## Description

<!-- Provide a brief description of the changes in this PR -->

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Database schema change
- [ ] Documentation update
- [ ] CI/CD or infrastructure change

## Related Issues

<!-- Link to related issues using #issue_number -->

Closes #

## Changes Made

<!-- List the main changes introduced by this PR -->

-
-
-

---

## Database Schema Changes (If Applicable)

<!-- If this PR includes database schema changes, complete the section below -->

### Schema Change Summary

- [ ] New tables created
- [ ] Existing tables modified
- [ ] Indexes added/modified
- [ ] RLS policies updated
- [ ] KG nodes/edges added
- [ ] Migration file created

### Canonical Schema Compliance Checklist

**Location & Source of Truth**
- [ ] Changes reflected in `docs/DATA_MODEL.md`
- [ ] Changes implemented in `packages/db/sql/*.sql`
- [ ] No ad-hoc DDL outside canonical SQL files
- [ ] Migration file follows naming convention: `NN_descriptive_name.sql`

**Naming & Types**
- [ ] All identifiers use `snake_case` (no camelCase/PascalCase)
- [ ] ID fields use `uuid PRIMARY KEY DEFAULT gen_random_uuid()`
- [ ] Timestamps use `timestamptz DEFAULT now()`
- [ ] Embeddings use `vector(1536)` with `model text` column
- [ ] Freeform fields use `jsonb` (e.g., `metadata`, `config`, `props`)

**Multi-Tenancy & RLS**
- [ ] Tables have `tenant_id uuid NOT NULL` column
- [ ] Tables have `workspace_id uuid` if workspace-scoped
- [ ] RLS policies enforce tenant isolation
- [ ] RLS policies use `current_setting('app.current_tenant_id')`
- [ ] Foreign keys include `tenant_id` for cross-table consistency

**Relationships**
- [ ] Foreign keys follow canonical entity graph
- [ ] All FKs have explicit `ON DELETE CASCADE` or `ON DELETE RESTRICT`
- [ ] No "shadow" tables duplicating canonical entities
- [ ] RAG tables reference parent tables correctly
- [ ] KG relationships use `kg.nodes.slug` as external key

**Indexing & Performance**
- [ ] Foreign key columns have indexes
- [ ] Lookup fields (slug, type, status) have indexes
- [ ] Vector columns use IVFFlat indexing
- [ ] Multi-tenant queries have composite indexes

**Validation**
- [ ] `make check-naming` passes
- [ ] `make validate-schema` passes
- [ ] `make check-rls` passes
- [ ] `make db-smoke` passes
- [ ] Manual RLS test completed

### Migration Safety

- [ ] Migration is idempotent (safe to re-run)
- [ ] Migration handles existing data gracefully
- [ ] No DROP operations (or carefully justified)
- [ ] Tested on local database

### Documentation

- [ ] `DATA_MODEL.md` updated with new tables/columns
- [ ] ERD updated (if relationships changed)
- [ ] RLS policies documented
- [ ] Migration notes added

### Validation Commands Run

```bash
# Add output of these commands
make check-naming
make validate-schema
make check-rls
make db-smoke
```

<!-- Paste command output here -->

---

## Testing

### Test Coverage

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] E2E tests added/updated (if applicable)
- [ ] Test coverage ≥80%

### Manual Testing

<!-- Describe the manual testing performed -->

- [ ] Tested locally
- [ ] Tested in staging environment
- [ ] Tested with real data

### Test Results

```bash
# Paste test output
npm test
```

---

## Code Quality

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] No console.log or debugging code left
- [ ] No hardcoded credentials or secrets
- [ ] TypeScript types are complete and accurate

---

## Documentation

- [ ] README updated (if applicable)
- [ ] API documentation updated (if applicable)
- [ ] Inline code comments added
- [ ] CHANGELOG updated

---

## Deployment

### Deployment Checklist

- [ ] Environment variables documented
- [ ] Database migrations tested
- [ ] Rollback plan documented
- [ ] Monitoring/alerting configured (if applicable)

### Deployment Notes

<!-- Any special instructions for deployment -->

---

## Screenshots (If Applicable)

<!-- Add screenshots for UI changes -->

---

## Reviewer Guidance

<!-- Specific areas reviewers should focus on -->

### Key Areas for Review

1.
2.
3.

### Questions for Reviewers

<!-- Any specific questions or concerns -->

---

## References

- [Canonical Schema Checklist](docs/CANONICAL_SCHEMA_CHECKLIST.md)
- [Canonical Schema Auditor](docs/CANONICAL_SCHEMA_AUDITOR_PROMPT.md)
- [Data Model Specification](docs/DATA_MODEL.md)
- [Deployment Guide](docs/kg_schema_deployment.md)

---

## Pre-Merge Checklist

- [ ] All CI checks passing
- [ ] At least one approval from code owner
- [ ] No merge conflicts
- [ ] Branch is up to date with main
- [ ] All comments addressed
- [ ] Documentation complete
- [ ] Tests passing
- [ ] Schema validation passing (if applicable)

---

## Sign-Off

**I confirm that:**
- [ ] This PR follows all canonical schema rules (if applicable)
- [ ] All tests pass locally
- [ ] Documentation is complete and accurate
- [ ] Code is production-ready

**Author:** @<!-- your-github-username -->
**Reviewer(s):** <!-- will be filled by reviewers -->
