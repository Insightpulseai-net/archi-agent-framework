---
name: deployment-orchestrator
description: Orchestrate multi-stage deployment (dev → staging → production). Sequence migrations, validate environments, run health checks, coordinate rollbacks. Use when deploying to production or managing release pipelines.
license: Apache-2.0
metadata:
  author: insightpulseai
  version: "1.0"
  domain: deployment
  platforms: ["digitalocean", "supabase", "github-actions"]
---

# Deployment Orchestrator Skill

Coordinate safe, automated deployments.

## Purpose

This agent manages the complete deployment lifecycle from development through production, ensuring all quality gates pass and rollback procedures are in place.

## How to Use

1. **Input artifact version** and target environment
2. **Verify all tests passing** (from ValidationAgent)
3. **Agent sequences deployment** (migrations → functions → RLS)
4. **Runs post-deploy health checks**
5. **Prepares rollback plan** if needed

## Deployment Pipeline

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│   DEV    │────▶│  STAGING │────▶│   UAT    │────▶│   PROD   │
│          │     │          │     │          │     │          │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                │                │
     ▼                ▼                ▼                ▼
  Unit Tests     Integration      Smoke Tests     Health Checks
  Lint/Format    E2E Tests        UAT Sign-off    Monitoring
```

## Deployment Sequence

### Stage 1: Pre-Flight Checks
```yaml
pre_flight:
  - name: Verify all tests passing
    command: pytest --cov=src --cov-fail-under=90
    blocking: true

  - name: Check migrations can apply
    command: supabase db diff --linked
    blocking: true

  - name: Validate secrets configured
    command: ./scripts/check-secrets.sh
    blocking: true

  - name: Verify Odoo module dependencies
    command: python -c "import odoo; odoo.modules.check_manifest()"
    blocking: true
```

### Stage 2: Schema Deployment
```yaml
schema_deploy:
  - name: Backup current database
    command: supabase db dump --file backup-$(date +%Y%m%d).sql

  - name: Apply migrations
    command: supabase db push

  - name: Verify schema integrity
    command: supabase db lint
```

### Stage 3: Function Deployment
```yaml
function_deploy:
  - name: Deploy Edge Functions
    command: supabase functions deploy --all

  - name: Deploy stored procedures
    command: psql -f migrations/functions.sql

  - name: Test RPC endpoints
    command: ./scripts/test-rpc.sh
```

### Stage 4: RLS Enforcement
```yaml
rls_deploy:
  - name: Apply RLS policies
    command: psql -f migrations/rls-policies.sql

  - name: Test with admin role
    command: ./scripts/test-rls.sh --role admin

  - name: Test with approver role
    command: ./scripts/test-rls.sh --role approver

  - name: Test with employee role
    command: ./scripts/test-rls.sh --role employee
```

### Stage 5: Health Checks
```yaml
health_checks:
  - name: Database connectivity
    endpoint: /health/db
    expected: 200
    timeout: 5s

  - name: Edge Function responses
    endpoint: /health/functions
    expected: 200
    timeout: 10s

  - name: RLS policies enforced
    endpoint: /health/rls
    expected: 200
    timeout: 5s

  - name: Odoo webhook connectivity
    endpoint: /health/odoo
    expected: 200
    timeout: 15s
```

## Rollback Procedure

```yaml
rollback:
  triggers:
    - health_check_failure
    - error_rate_spike (>1%)
    - latency_spike (p99 > 5s)

  steps:
    - name: Revert migrations
      command: supabase db reset --version $PREVIOUS_VERSION

    - name: Restore from backup
      command: psql < backup-$PREVIOUS_DATE.sql

    - name: Notify on-call
      command: ./scripts/notify-oncall.sh "Rollback triggered: $REASON"

    - name: Create incident
      command: ./scripts/create-incident.sh
```

## Environment Configuration

### Development
```yaml
environment: dev
supabase_project: ipai-dev
odoo_url: https://erp-dev.insightpulseai.net
auto_deploy: true
require_approval: false
```

### Staging
```yaml
environment: staging
supabase_project: ipai-staging
odoo_url: https://erp-staging.insightpulseai.net
auto_deploy: false
require_approval: false
```

### Production
```yaml
environment: prod
supabase_project: ipai-prod
odoo_url: https://erp.insightpulseai.net
auto_deploy: false
require_approval: true
approvers:
  - @devops-lead
  - @engineering-manager
```

## GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production

jobs:
  pre-flight:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest --cov=src --cov-fail-under=90

      - name: Lint and format
        run: |
          ruff check src
          black --check src

  deploy-staging:
    needs: pre-flight
    if: github.event.inputs.environment == 'staging' || github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Setup Supabase CLI
        uses: supabase/setup-cli@v1

      - name: Link project
        run: supabase link --project-ref ${{ secrets.SUPABASE_PROJECT_REF }}

      - name: Apply migrations
        run: supabase db push

      - name: Deploy Edge Functions
        run: supabase functions deploy --all

      - name: Health check
        run: ./scripts/health-check.sh staging

  deploy-production:
    needs: deploy-staging
    if: github.event.inputs.environment == 'production'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Backup database
        run: supabase db dump --file backup-$(date +%Y%m%d).sql

      - name: Apply migrations
        run: supabase db push

      - name: Deploy Edge Functions
        run: supabase functions deploy --all

      - name: Deploy Odoo modules
        run: |
          ssh odoo@erp.insightpulseai.net "
            cd /opt/odoo/addons &&
            git pull origin main &&
            supervisorctl restart odoo
          "

      - name: Health check
        run: ./scripts/health-check.sh production

      - name: Notify Slack
        run: |
          curl -X POST ${{ secrets.SLACK_WEBHOOK }} \
            -d '{"text": "✅ Production deployment complete: ${{ github.sha }}"}'
```

## Deployment Checklist

```markdown
## Pre-Deployment Checklist

### Code Quality
- [ ] All tests passing (unit ≥90%, integration ≥80%)
- [ ] Code review approved (2+ reviewers)
- [ ] No HIGH/CRITICAL security issues
- [ ] Lint and format checks pass

### Environment
- [ ] Staging deployment successful
- [ ] Smoke tests green on staging
- [ ] UAT sign-off received (if required)
- [ ] Migrations tested on staging data

### Infrastructure
- [ ] Migrations backed up
- [ ] Rollback plan documented
- [ ] Health checks configured
- [ ] On-call engineer available

### Communication
- [ ] Deployment window confirmed
- [ ] Stakeholders notified
- [ ] Slack channel ready
- [ ] Incident response team on standby

## Post-Deployment Checklist

### Verification
- [ ] Health checks passing
- [ ] Logs show no errors
- [ ] Metrics within normal range
- [ ] Critical paths manually tested

### Monitoring
- [ ] Dashboards updated
- [ ] Alerts configured
- [ ] SLA tracking enabled
- [ ] Error tracking enabled

### Documentation
- [ ] Release notes published
- [ ] Changelog updated
- [ ] Runbook updated (if needed)
- [ ] Post-mortem scheduled (if issues)
```

## Skill Boundaries

### What This Skill CAN Do
- Sequence deployment stages
- Run pre-flight checks
- Apply database migrations
- Deploy Edge Functions
- Execute health checks
- Coordinate rollbacks
- Generate deployment scripts

### What This Skill CANNOT Do
- Extract specs from docs (use `documentation-parser`)
- Validate compliance (use `compliance-validator`)
- Generate application code (use `code-generator`)
- Write SQL queries (use `sql-agent`)
- Run tests (use `validation-agent`)

## Rules

- Never deploy without tests passing
- Always backup before migration
- Run health checks post-deploy
- Wait for on-call confirmation before prod deploy
- **DO NOT** skip validation steps
- **DO NOT** deploy untested code to production
- **DO NOT** proceed if health checks fail
- **DO NOT** force-push to production
