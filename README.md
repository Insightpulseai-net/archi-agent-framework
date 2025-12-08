# Agent Layer - Multi-Agent Orchestration System

**Purpose**: LangGraph-based multi-agent orchestration with Qdrant vector search, Langfuse observability, and comprehensive safety harnesses.

**Version**: 1.0.0
**Last Updated**: 2025-12-08
**Stack**: LangGraph, Qdrant, Langfuse, FastAPI, LiteLLM

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Workbench Frontend                     │
│              (Next.js + Material Web)                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                 Agent Runtime (FastAPI)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Research   │  │   Expense    │  │ Finance SSC  │      │
│  │    Agent     │  │  Classifier  │  │    Agent     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            ▼                                 │
│              ┌─────────────────────────┐                     │
│              │   LangGraph State      │                     │
│              │   Management Layer     │                     │
│              └─────────────────────────┘                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Qdrant     │ │  Langfuse    │ │   LiteLLM    │
│  (Vectors)   │ │ (Observ.)    │ │  (Gateway)   │
└──────────────┘ └──────────────┘ └──────────────┘
        │                               │
        ▼                               ▼
┌──────────────┐                 ┌──────────────┐
│  Supabase    │                 │ Claude/GPT-4 │
│   (Data)     │                 │   (LLMs)     │
└──────────────┘                 └──────────────┘
```

---

## Directory Structure

```
agent-layer/
├── langgraph-agents/           # LangGraph agent implementations
│   ├── agents/
│   │   ├── research_agent.py   # Multi-step research agent
│   │   ├── expense_classifier.py  # OCR → category classification
│   │   └── finance_ssc_agent.py   # BIR form generation
│   ├── graphs/
│   │   ├── research_graph.py   # Research workflow graph
│   │   └── expense_graph.py    # Expense processing graph
│   ├── tools/
│   │   ├── supabase_tool.py    # Supabase query tool
│   │   ├── qdrant_tool.py      # Vector search tool
│   │   └── odoo_tool.py        # Odoo XML-RPC tool
│   ├── state/
│   │   ├── agent_state.py      # State schemas
│   │   └── message_state.py    # Message handling
│   └── README.md
├── qdrant/                     # Vector search setup
│   ├── collections/
│   │   └── knowledge_base.json # Collection schema
│   ├── ingest/
│   │   ├── document_chunker.py # Document chunking
│   │   └── embedding_generator.py  # OpenAI embeddings
│   ├── query/
│   │   └── semantic_search.py  # Search API
│   ├── docker-compose.yml      # Qdrant deployment
│   └── README.md
├── langfuse/                   # Observability setup
│   ├── docker-compose.yml      # Langfuse deployment
│   ├── integrations/
│   │   ├── litellm.py          # LiteLLM tracing
│   │   └── langgraph.py        # LangGraph tracing
│   ├── dashboards/
│   │   └── cost_dashboard.json # Cost/latency dashboard
│   ├── alerts/
│   │   └── budget_alerts.py    # Budget threshold alerts
│   └── README.md
├── safety/                     # Safety harnesses
│   ├── prompt_injection_detector.py  # Injection detection
│   ├── content_moderator.py    # Content moderation
│   ├── rate_limiter.py         # Rate limiting
│   ├── kill_switch.py          # Emergency stop
│   ├── audit_logger.py         # Security logging
│   └── README.md
├── bindings/                   # Agent bindings to Gold schemas
│   ├── saricoach_binding.py    # SariCoach agent binding
│   ├── genieview_binding.py    # GenieView NL2SQL binding
│   ├── schema_mapper.py        # Gold table → context
│   ├── role_generator.py       # Read-only SQL roles
│   └── README.md
├── services/                   # FastAPI runtime
│   ├── agent-runtime/
│   │   ├── main.py             # FastAPI app
│   │   ├── routers/
│   │   │   ├── agents.py       # Agent execution routes
│   │   │   └── health.py       # Health check routes
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── docker-compose.yml
├── tests/                      # Integration tests
│   ├── test_research_agent.py
│   ├── test_expense_classifier.py
│   ├── test_safety_harnesses.py
│   └── test_qdrant_search.py
├── infra/                      # Infrastructure configs
│   └── do/
│       └── agent-runtime.yaml  # DO App Platform spec
└── README.md
```

---

## Quick Start

### 1. Deploy Qdrant
```bash
cd qdrant
docker-compose up -d
```

### 2. Deploy Langfuse
```bash
cd langfuse
docker-compose up -d
```

### 3. Setup Agent Runtime
```bash
cd services/agent-runtime
pip install -r requirements.txt
uvicorn main:app --reload
```

### 4. Ingest Knowledge Base
```bash
cd qdrant/ingest
python document_chunker.py --input docs/ --output chunks.json
python embedding_generator.py --input chunks.json --output embeddings.json
```

### 5. Test Agent
```bash
curl -X POST http://localhost:8000/api/agents/run \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "research-agent",
    "query": "What are the top expense categories last month?",
    "user_id": "user-123"
  }'
```

---

## Agent Types

### 1. Research Agent
**Purpose**: Multi-step research with knowledge base retrieval

**Workflow**:
```
Entry → Search Qdrant → Fetch Context → Generate Answer → Validate → Retry (if needed)
```

**Use Cases**:
- Analyze Scout transaction trends
- Research BIR filing requirements
- Compare vendors by expense amounts

### 2. Expense Classifier
**Purpose**: OCR → category classification with policy validation

**Workflow**:
```
Entry → OCR Extract → Validate → Classify Category → Route to Approval → Notify
```

**Use Cases**:
- Classify receipts from PaddleOCR-VL
- Route expenses to correct approval workflow
- Flag policy violations

### 3. Finance SSC Agent
**Purpose**: BIR form generation and multi-employee finance operations

**Workflow**:
```
Entry → Query Odoo → Aggregate Tax Data → Generate BIR Form → Store → Notify
```

**Use Cases**:
- Generate 1601-C monthly
- Generate 2550Q quarterly
- Multi-employee tax calculations

---

## Safety Harnesses

### 1. Prompt Injection Detection
- **Regex Patterns**: 10+ injection patterns
- **LlamaGuard**: AI-based detection
- **Action**: Block + audit log

### 2. Content Moderation
- **OpenAI Moderation API**: Automatic flagging
- **Categories**: hate, harassment, violence, sexual
- **Action**: Block + notify admin

### 3. Rate Limiting
- **Per User**: 100 requests/hour
- **Global**: 1000 requests/hour
- **Action**: Return 429 + suggest retry

### 4. Budget Limits
- **Per Agent**: $1 per run (configurable)
- **Per Project**: $100/day
- **Action**: Pause agent + alert

### 5. Kill Switch
- **Manual**: Admin dashboard button
- **Auto**: Budget exceeded or rate limit breached
- **Action**: Stop all agents + notify

---

## Observability

### Langfuse Traces
**Captured Data**:
- Input prompt
- Output response
- Model used (claude-sonnet-4.5, gpt-4, etc.)
- Tokens (prompt + completion)
- Cost (USD)
- Latency (ms)

**Tags**:
- `agent_type`: research, expense, finance
- `user_id`: User identifier
- `session_id`: Session tracking
- `environment`: dev, staging, production

**Annotations**:
- Human feedback (thumbs up/down)
- Error flags (timeout, rate limit)
- Quality scores (confidence, relevance)

### Cost Dashboard
**Metrics**:
- Total cost today
- Cost per agent
- Cost per model
- Cost per user

**Alerts**:
- Budget threshold exceeded (email + Mattermost)
- Unusual spike in cost (auto-investigation)
- Model failure (fallback triggered)

---

## Agent Bindings

### SariCoach Binding
**Purpose**: Bind SariCoach agent to Scout gold tables

**Gold Tables**:
- `gold.finance_expenses`
- `gold.finance_vendors`
- `gold.scout_transactions`

**Context**:
```python
{
  "tables": ["gold.finance_expenses"],
  "columns": ["vendor", "amount", "category", "date"],
  "filters": ["status = 'approved'", "date > '2025-01-01'"],
  "aggregations": ["SUM(amount)", "COUNT(*)"]
}
```

### GenieView Binding
**Purpose**: Natural language to SQL (NL2SQL) for Tableau

**Workflow**:
1. User query: "Show me top 5 vendors by expense amount"
2. Agent → Qdrant: Find similar queries
3. Agent → LLM: Generate SQL
4. Agent → Supabase: Execute SQL
5. Agent → User: Results + SQL

**SQL Role**:
```sql
CREATE ROLE genieview_readonly;
GRANT SELECT ON gold.* TO genieview_readonly;
REVOKE INSERT, UPDATE, DELETE ON gold.* FROM genieview_readonly;
```

---

## Testing

### Unit Tests
```bash
pytest tests/test_research_agent.py -v
pytest tests/test_expense_classifier.py -v
```

### Integration Tests
```bash
pytest tests/ -v --cov=langgraph-agents
```

### Safety Tests
```bash
pytest tests/test_safety_harnesses.py -v
```

---

## Deployment

### DigitalOcean App Platform
```bash
doctl apps create --spec infra/do/agent-runtime.yaml
```

### Kubernetes (DOKS)
```bash
kubectl apply -f k8s/agent-runtime-deployment.yaml
```

---

## Configuration

### Environment Variables
```bash
# Supabase
export SUPABASE_URL="https://xkxyvboeubffxxbebsll.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="..."

# Qdrant
export QDRANT_URL="http://qdrant:6333"

# Langfuse
export LANGFUSE_URL="http://langfuse:3000"
export LANGFUSE_PUBLIC_KEY="..."
export LANGFUSE_SECRET_KEY="..."

# LiteLLM
export LITELLM_URL="https://litellm.insightpulseai.net"
export LITELLM_API_KEY="..."

# Odoo
export ODOO_URL="https://odoo.insightpulseai.net"
export ODOO_DB="production"
export ODOO_USERNAME="admin"
export ODOO_PASSWORD="..."

# OpenAI (for embeddings + moderation)
export OPENAI_API_KEY="..."
```

---

## Performance

### Latency Targets
- **Agent Execution**: <5s (p95)
- **Vector Search**: <100ms (p95)
- **LLM Call**: <3s (p95)

### Throughput
- **Concurrent Agents**: 50+
- **Requests/min**: 500+
- **Vector Searches/s**: 100+

---

## Security

### Authentication
- API keys (Supabase JWT)
- Rate limiting per user
- RLS policies enforced

### Secrets Management
- Supabase Vault
- Environment variables only
- No hardcoded secrets

### Audit Logging
- All agent runs logged
- Security events flagged
- Suspicious activity alerts

---

## Next Steps

1. **T7.1**: Setup LiteLLM Gateway (see `prd.md`)
2. **T7.2**: Integrate Langfuse
3. **T7.3**: Build Genie Chat Interface
4. **T7.4**: Create Agent Registry Page
5. **T7.5**: Implement Tool Library
6. **T7.6**: Build LangGraph Agent Runtime
7. **T7.7**: Create Agent Run Timeline
8. **T7.8**: Build Cost Tracking Dashboard
9. **T7.9**: Implement Budget Alerts

---

## References

- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [Qdrant Docs](https://qdrant.tech/documentation/)
- [Langfuse Docs](https://langfuse.com/docs)
- [LiteLLM Docs](https://docs.litellm.ai/)
- [PRD](../spec-kit/spec/ai-workbench/prd.md)
- [Tasks](../spec-kit/spec/ai-workbench/tasks.md)
