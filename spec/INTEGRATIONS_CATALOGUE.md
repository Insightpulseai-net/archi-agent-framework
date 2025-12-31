# Docs2Code → GitHub Developer Program Integration Catalogue

**Purpose**: Map Docs2Code agents to GitHub integrations (Apps, Webhooks, OAuth) for enterprise discoverability and compliance.

**Registry**: github.com/settings/apps (managed)  
**Discoverability**: GitHub Marketplace (candidate)  
**Support**: integrations@insightpulseai.net

---

## Integration Matrix

| Agent | Integration Type | GitHub App | Webhook Events | Scopes | Use Case | Status |
|-------|------------------|-----------|-----------------|---------|----------|--------|
| **DocumentationParser** | Custom App | `pulser-docs-ingester` | `push`, `pull_request` | `contents:read` | Crawl repo docs on commits | MVP |
| **ComplianceValidator** | GitHub App | `pulser-compliance-gate` | `pull_request`, `status` | `checks:write`, `contents:read` | Block non-compliant PRs | MVP |
| **CodeGenerator** | Webhook Receiver | `pulser-codegen-executor` | `issues`, `discussion` | `contents:write`, `pull_requests:write` | Generate code from issues | MVP |
| **SQLAgent** | Custom Action | n/a | `push` (migrations/) | `contents:write` | Validate/test SQL migrations | Backlog |
| **ValidationAgent** | GitHub Action | `action-pytest-coverage` | `pull_request` | `checks:write` | Enforce 90%+ coverage gates | MVP |
| **DeploymentOrchestrator** | Release App | `pulser-release-mgr` | `release`, `deployment` | `deployments:write`, `contents:read` | Blue/green deploys | MVP |

---

## 1. DocumentationParser: `pulser-docs-ingester`

**Type**: GitHub App (Custom)  
**Purpose**: Automatically extract and catalog docs on repo changes

### Webhook Handler (n8n)
```
Event: push branch:main path:docs/**
→ Trigger DocumentationParser
→ Extract AST → Store docs_raw in Supabase
→ Emit pgvector embeddings
→ Post summary comment on PR
```

---

## 2. ComplianceValidator: `pulser-compliance-gate`

**Type**: GitHub App (Check Runs + Status)  
**Purpose**: Gate PRs on regulatory compliance (BIR, PFRS, DOLE)

### Workflow
```
On PR:
1. Fetch compliance_rules table (Supabase)
2. Parse PR diff → extract regulatory entities
3. Check against BIR_1700, PFRS_16, DOLE rules
4. POST check_run with status (pass/fail)
5. If FAIL: Comment with remediation steps
6. Block merge if required_status_check=true
```

---

## 3. CodeGenerator: `pulser-codegen-executor`

**Type**: GitHub App + Issue Templates  
**Purpose**: Generate code from GitHub issues (issue-driven development)

### Workflow
```
On issue labeled "codegen:module":
1. Parse issue body (structured template)
2. Extract module spec (fields, workflows, compliance rules)
3. Call CodeGenerator agent
4. Generate Odoo module (native 80%, OCA 15%, custom 5%)
5. Create PR with generated code
6. Request compliance review
```

---

## 4. ValidationAgent: `action-pytest-coverage`

**Type**: GitHub Action  
**Purpose**: Enforce TDD gates (90% unit, 80% integration)

### Workflow Integration
```yaml
on: [pull_request]

jobs:
  coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: insightpulseai/action-pytest-coverage@v1
        with:
          min_unit_coverage: 90
          min_integration_coverage: 80
          fail_on_below_threshold: true
```

---

## 5. DeploymentOrchestrator: `pulser-release-mgr`

**Type**: GitHub App (Release + Deployment)  
**Purpose**: Blue/green deploys on DigitalOcean with auto-rollback

### Workflow
```
On release created:
1. Get artifact list from release body
2. Validate all artifacts passed tests
3. Create DO blue environment
4. Deploy artifacts to blue
5. Run health checks (5 retries)
6. Promote blue → green (DNS switch)
7. Monitor 10min
8. On failure: Auto-rollback to previous green
9. Emit DPO pair if failure occurred
```

---

## Quick Links

- **Register App**: https://github.com/settings/apps
- - **GitHub Marketplace**: https://github.com/marketplace
  - - **Integration Docs**: https://docs.github.com/integrations
    - - **API Reference**: https://docs.github.com/rest
      - - **Webhook Events**: https://docs.github.com/webhooks-and-events/webhooks/webhook-events-and-payloads
       
        - ---

        ## Implementation Status

        ✅ Spec complete
        ⏳ GitHub Apps (5) - register at github.com/settings/apps
        ⏳ n8n workflows - deploy when apps created
        ⏳ GitHub Marketplace listing - submit after testing
        
