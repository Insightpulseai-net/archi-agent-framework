# Data Engineering Workbench - n8n Workflows

This directory contains n8n workflow templates for integrating the Data Engineering Workbench with external services.

## Workflows Overview

### 1. Month-End Finance Pipeline (`month-end-finance.json`)

**Purpose**: Automated month-end financial data extraction and reporting.

**Trigger**: Scheduled (1st of each month at 6 AM UTC)

**Flow**:
1. Authenticate with Odoo CE/OCA 18
2. Extract GL transactions for the previous month
3. Extract AP (Accounts Payable) data
4. Generate summary statistics
5. Push data to Superset for visualization
6. Send Slack notification with summary
7. Log completion to workbench

**Required Environment Variables**:
```
ODOO_URL=https://erp.insightpulseai.net
ODOO_DB=odoo
ODOO_USER=<your-odoo-user>
ODOO_API_KEY=<your-odoo-api-key>
SUPERSET_URL=https://superset.insightpulseai.net
SUPERSET_FINANCE_DATASET_ID=<dataset-id>
WORKBENCH_API_URL=https://workbench.insightpulseai.net
SLACK_WEBHOOK_URL=<your-slack-webhook>
```

**To Import**:
1. Go to n8n UI → Workflows → Import from File
2. Select `month-end-finance.json`
3. Configure credentials:
   - Create "Workbench API Key" HTTP Header Auth credential
   - Set up Slack webhook (if using notifications)
4. Activate the workflow

---

### 2. OCR to Odoo Expense (`ocr-to-odoo-expense.json`)

**Purpose**: Process uploaded documents via OCR and create expense records in Odoo.

**Trigger**: HTTP Webhook (POST to `/webhook/ocr-expense`)

**Flow**:
1. Receive document upload
2. Store document in MinIO/S3
3. Call OCR service for text extraction
4. Map extracted data to expense format
5. Check confidence score:
   - **High confidence (≥85%)**: Create expense directly in Odoo
   - **Low confidence (<85%)**: Queue for manual review
6. Send notifications and log results

**Required Environment Variables**:
```
OCR_SERVICE_URL=http://188.166.237.231:8080
OCR_API_KEY=<your-ocr-api-key>
ODOO_URL=https://erp.insightpulseai.net
ODOO_DB=odoo
ODOO_USER=<your-odoo-user>
ODOO_API_KEY=<your-odoo-api-key>
WORKBENCH_API_URL=https://workbench.insightpulseai.net
WORKBENCH_DB_CONNECTION_ID=<connection-uuid>
SLACK_WEBHOOK_URL=<your-slack-webhook>
```

**Required Credentials**:
- MinIO/S3 credentials for document storage
- Workbench API Key for database operations

**Example Request**:
```bash
curl -X POST https://n8n.insightpulseai.net/webhook/ocr-expense \
  -H "Content-Type: multipart/form-data" \
  -F "file=@receipt.pdf"
```

---

### 3. Agent Orchestrator (`agent-orchestrator.json`)

**Purpose**: Route tasks to AI agents (odoo-developer, finance-ssc, devops, bi-architect).

**Trigger**: HTTP Webhook (POST to `/webhook/agent-task`)

**Flow**:
1. Validate task request
2. Log task start
3. Route to appropriate agent via MCP
4. Handle response:
   - **Success**: Log result, return response
   - **Failure**: Retry with exponential backoff (up to 3 attempts)
5. Send notifications for failures

**Required Environment Variables**:
```
MCP_URL=https://mcp.insightpulseai.net
MCP_API_KEY=<your-mcp-api-key>
ODOO_DEVELOPER_AGENT_URL=<optional-override>
FINANCE_SSC_AGENT_URL=<optional-override>
DEVOPS_AGENT_URL=<optional-override>
BI_ARCHITECT_AGENT_URL=<optional-override>
WORKBENCH_API_URL=https://workbench.insightpulseai.net
WORKBENCH_DB_CONNECTION_ID=<connection-uuid>
SLACK_WEBHOOK_URL=<your-slack-webhook>
N8N_WEBHOOK_URL=https://n8n.insightpulseai.net/webhook
```

**Available Agents**:
| Agent | Capabilities |
|-------|-------------|
| `odoo-developer` | Code generation, module creation, bug fixes |
| `finance-ssc` | Report analysis, reconciliation, audit support |
| `devops` | Deployment, monitoring, infrastructure |
| `bi-architect` | Dashboard design, query optimization, data modeling |

**Example Request**:
```bash
curl -X POST https://n8n.insightpulseai.net/webhook/agent-task \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "odoo-developer",
    "task_type": "code_generation",
    "payload": {
      "request": "Create a custom report for AP aging by vendor",
      "context": {
        "module": "account_reports",
        "odoo_version": "18.0"
      }
    },
    "priority": "normal"
  }'
```

---

## Setup Instructions

### 1. Install n8n

If not already installed, see the main infrastructure setup:
```bash
cd /opt/workbench/infra
docker compose -f docker-compose.workbench.yml up -d
```

Or standalone n8n:
```bash
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -e N8N_BASIC_AUTH_ACTIVE=true \
  -e N8N_BASIC_AUTH_USER=admin \
  -e N8N_BASIC_AUTH_PASSWORD=<password> \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n
```

### 2. Configure Environment Variables

In n8n UI:
1. Go to Settings → Environment Variables
2. Add all required variables from each workflow

Or set in `.env` file for Docker:
```bash
# Add to .env.workbench
ODOO_URL=https://erp.insightpulseai.net
ODOO_DB=odoo
# ... etc
```

### 3. Import Workflows

```bash
# Via n8n CLI (if available)
n8n import:workflow --input=workflows/month-end-finance.json
n8n import:workflow --input=workflows/ocr-to-odoo-expense.json
n8n import:workflow --input=workflows/agent-orchestrator.json
```

Or manually via UI: Workflows → Import from File

### 4. Configure Credentials

Each workflow requires these credential types:
- **HTTP Header Auth** (`workbench-api-key`): For Workbench API calls
- **S3** (`minio-credentials`): For document storage (OCR workflow)
- **Slack** (optional): For notifications

### 5. Activate Workflows

After importing and configuring:
1. Open each workflow
2. Click the toggle to activate
3. For webhook workflows, note the webhook URL

---

## Monitoring & Troubleshooting

### View Execution History
- n8n UI → Executions
- Filter by workflow, status, date range

### Common Issues

**Authentication Errors**:
- Verify environment variables are set
- Check credential configuration
- Ensure API keys have correct permissions

**Timeout Errors**:
- Increase timeout in HTTP Request nodes
- Check target service availability
- Review network connectivity

**Data Format Errors**:
- Check input data structure
- Review Code node transformations
- Enable debug logging

### Logs

Docker logs:
```bash
docker logs n8n -f
```

Execution logs in n8n UI show step-by-step data flow.

---

## Customization

### Adding New Agents

Edit the `agent-orchestrator.json` Code node to add agents:
```javascript
const agents = {
  // ... existing agents
  'new-agent': {
    url: $env.NEW_AGENT_URL || `${$env.MCP_URL}/agents/new-agent`,
    timeout: 60000,
    capabilities: ['capability1', 'capability2']
  }
};
```

### Modifying Schedules

Edit the Schedule Trigger node:
- `0 6 1 * *` = 6 AM on 1st of each month
- `0 0 * * *` = Daily at midnight
- `0 */6 * * *` = Every 6 hours

### Adding Error Notifications

Each workflow has error handling. To add custom notifications:
1. Add Error Trigger node
2. Connect to notification node (Slack, Email, etc.)
3. Configure notification content

---

## Security Notes

1. **Never commit credentials** - Use environment variables
2. **Restrict webhook access** - Use API keys or IP filtering
3. **Audit access** - Review n8n execution logs regularly
4. **Rotate secrets** - Update API keys quarterly

---

## Support

For issues:
1. Check n8n documentation: https://docs.n8n.io
2. Review workbench logs: `/opt/workbench/logs`
3. Contact platform team via Slack #data-engineering
