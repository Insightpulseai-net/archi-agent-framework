# Slack Marketplace → Pulser Agent Framework Integration Catalogue

**Purpose**: Map installed Slack apps to Pulser Agent Framework workflows, n8n automation, and Docs2Code pipeline integration.

**Registry**: `spec/SLACK_APPS_REGISTRY.json`
**Workspace Admin**: https://app.slack.com/manage
**Support**: integrations@insightpulseai.net

---

## Installed Apps Overview

| App | Vendor | Type | Status | Primary Use Case |
|-----|--------|------|--------|------------------|
| **Claude** | Anthropic | AI Assistant | ✅ Installed | Code review, documentation, compliance Q&A |
| **ChatGPT** | OpenAI | AI Assistant | ✅ Installed | Research, drafting, translation |
| **GitHub** | GitHub, Inc. | Developer Tool | ✅ Installed | PR notifications, issue tracking, deployments |
| **Google Drive** | Google | Productivity | ✅ Installed | File sharing, Docs2Code ingestion trigger |

---

## Integration Matrix

| Slack App | n8n Workflow | Pulser Agent | Supabase Table | Use Case |
|-----------|--------------|--------------|----------------|----------|
| Claude | `slack-claude-handler` | ComplianceValidator | `ai_interactions` | Compliance Q&A in channels |
| ChatGPT | `slack-chatgpt-handler` | — | `ai_interactions` | General assistance |
| GitHub | `slack-github-bridge` | CodeGenerator | `github_events` | Issue-to-code pipeline |
| Google Drive | `gdrive-ingest-trigger` | DocumentationParser | `docs_raw` | Docs2Code source ingestion |

---

## 1. Claude Integration

**App ID**: A04KGS7N9A8
**Type**: AI Assistant (Anthropic)
**Slash Command**: `/claude`

### Channel Configuration

| Channel | Purpose | Permissions |
|---------|---------|-------------|
| `#dev-prs` | Code review assistance | Read + Write |
| `#ops-alerts` | Incident analysis | Read + Write |
| `#docs` | Documentation generation | Read + Write |
| `#compliance` | Regulatory Q&A (BIR, PFRS, DOLE) | Read + Write |

### n8n Workflow Integration

```
Trigger: Slack Event (app_mention, message.im)
→ Extract message content
→ Check channel context (#compliance → ComplianceValidator mode)
→ Forward to Claude API with context
→ Store interaction in Supabase `ai_interactions`
→ Post response as thread reply
```

### Pulser Agent Mapping

- **Channel #compliance**: Routes to `ComplianceValidator` agent for regulatory questions
- **Channel #docs**: Routes to `DocumentationParser` for spec drafting
- **Other channels**: General Claude assistance

---

## 2. ChatGPT Integration

**App ID**: A04SK41B0HM
**Type**: AI Assistant (OpenAI)
**Slash Command**: `/chatgpt`

### Use Cases

| Use Case | Channel | Workflow |
|----------|---------|----------|
| Meeting summaries | `#general` | Parse meeting transcript → Generate bullet points |
| Research queries | Any | Quick fact-checking and research |
| Translation | `#international` | Filipino ↔ English translation |
| Email drafting | DM | Professional email generation |

### n8n Workflow Integration

```
Trigger: Slack slash command /chatgpt
→ Extract prompt from command
→ Forward to OpenAI API
→ Store in Supabase `ai_interactions`
→ Post response ephemerally or in channel
```

---

## 3. GitHub Integration

**App ID**: A8GBNUWU8
**Type**: Developer Tool
**Slash Command**: `/github`

### Repository Subscriptions

| Repository | Channel | Events |
|------------|---------|--------|
| `insightpulseai-net/pulser-agent-framework` | `#dev-prs` | `pulls`, `reviews`, `comments` |
| `insightpulseai-net/pulser-agent-framework` | `#ops-deploys` | `deployments`, `releases` |
| `insightpulseai-net/docs2code-pipeline` | `#dev-prs` | `pulls`, `reviews` |
| `insightpulseai-net/odoo-modules` | `#dev-issues` | `issues`, `issue_comments` |

### Slash Commands

```
/github subscribe insightpulseai-net/repo pulls
/github subscribe insightpulseai-net/repo deployments
/github close [issue-url]
/github open [owner/repo]
```

### Bridge to GitHub Apps Registry

The Slack GitHub app bridges to our custom GitHub Apps:

| GitHub App | Slack Notification |
|------------|-------------------|
| `pulser-docs-ingester` | Posts indexing summary to `#docs` |
| `pulser-compliance-gate` | Posts PR block/pass to `#dev-prs` |
| `pulser-codegen-executor` | Posts generated PR link to `#dev-prs` |
| `pulser-release-mgr` | Posts deployment status to `#ops-deploys` |

### n8n Workflow: Issue-to-Code Pipeline

```
Trigger: GitHub issue labeled "codegen:module"
→ GitHub App creates branch
→ Slack notification to assignee DM
→ CodeGenerator produces code
→ PR created
→ Slack notification to #dev-prs with AI summary
→ Request review via @mentions
```

---

## 4. Google Drive Integration

**App ID**: A6NL8MJ6Q
**Type**: Productivity
**Slash Command**: `/drive`

### File Unfurling

When Google Drive links are shared in Slack, the app automatically unfurls them with:
- File preview thumbnail
- Last modified timestamp
- Access level indicator
- Quick action buttons (Open, Request Access)

### Docs2Code Pipeline Integration

```
Trigger: Google Doc shared in #data-engineering or #docs
→ n8n webhook receives file metadata
→ Check if doc matches ingestion patterns (spec, prd, api-docs)
→ If match: Trigger DocumentationParser
→ Extract content via Google Docs API
→ Store in Supabase `docs_raw`
→ Generate pgvector embeddings
→ Post summary to original Slack thread
```

### Channel Permissions

| Channel | Drive Actions | Purpose |
|---------|---------------|---------|
| `#data-engineering` | Unfurl + Auto-ingest | Data pipeline specs |
| `#docs` | Unfurl + Auto-ingest | General documentation |
| `#general` | Unfurl only | General file sharing |
| `#finance` | Unfurl + Restricted | Financial documents (extra auth) |

---

## n8n Webhook Configuration

### Slack Event Subscriptions

```yaml
# n8n Credential: slack-oauth
# App: Pulser Slack Integration

Events:
  - app_mention
  - message.im
  - message.channels
  - link_shared
  - reaction_added

Webhook URL: https://n8n.insightpulseai.net/webhook/slack-events
```

### Workflow Templates

| Workflow | Trigger | Action | Target |
|----------|---------|--------|--------|
| `slack-to-github-issue` | Reaction `:github:` | Create GitHub issue | `pulser-codegen-executor` |
| `slack-ai-summary` | Reaction `:summarize:` | Claude summarizes thread | Thread reply |
| `slack-to-supabase` | Reaction `:save:` | Store message in knowledge base | `knowledge_snippets` |
| `gdrive-doc-ingest` | Link shared | Trigger DocumentationParser | `docs_raw` |

---

## Security & Compliance

### Data Handling

| Data Type | Retention | Storage | Compliance |
|-----------|-----------|---------|------------|
| AI conversations | 90 days | Supabase `ai_interactions` | GDPR, DPA 2012 |
| GitHub events | 1 year | Supabase `github_events` | SOC 2 |
| File metadata | 30 days | Supabase `file_shares` | Internal policy |

### Access Controls

```yaml
Admin Roles:
  - workspace_admin: Full app management
  - app_manager: Install/uninstall apps
  - channel_admin: Per-channel app permissions

Restricted Apps:
  - Finance channels: Require additional approval
  - HR channels: PII handling protocols
```

---

## Migration Path: Slack → Mattermost

Per `stack.yaml`, Mattermost is the designated self-hosted messaging platform. The following migration path is recommended:

### Phase 1: Parallel Operation
- Maintain Slack for external collaboration
- Deploy Mattermost for internal engineering
- Bridge critical channels via n8n

### Phase 2: Integration Migration
- Migrate n8n workflows to Mattermost webhooks
- Deploy Mattermost GitHub plugin
- Configure Mattermost AI plugins (Claude, ChatGPT equivalents)

### Phase 3: Full Migration (Optional)
- Archive Slack workspace
- Complete channel migration
- Update all documentation references

---

## Quick Links

- **Slack App Directory**: https://api.slack.com/apps
- **Slack Marketplace**: https://slack.com/apps
- **Slack API Docs**: https://api.slack.com/docs
- **Mattermost Migration**: https://docs.mattermost.com/administration/migrating.html
- **n8n Slack Node**: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.slack/

---

## Implementation Status

| Item | Status |
|------|--------|
| ✅ App inventory documented | Complete |
| ✅ Registry JSON created | Complete |
| ⏳ n8n webhook endpoints | Configure in n8n |
| ⏳ Channel subscriptions | Configure in Slack Admin |
| ⏳ Custom pulser-slack-bot | Backlog |
| ⏳ Workflow Steps integration | Backlog |
| ⏳ Mattermost migration plan | Documentation phase |
