# Supabase Architecture - External Managed Service

**Important**: Supabase is **NOT self-hosted** in this stack. It's a managed external service.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ External Services (Managed, Not Self-Hosted)          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Supabase PostgreSQL (xkxyvboeubffxxbebsll)             │
│   ├─ Direct connection: Port 5432                      │
│   ├─ Pooler: Port 6543 (Supavisor)                     │
│   └─ URL: xkxyvboeubffxxbebsll.supabase.co             │
│                                                         │
│ Supabase Services:                                     │
│   ├─ PostgREST API (auto-generated)                    │
│   ├─ Storage (S3-compatible)                           │
│   ├─ Auth (GoTrue)                                     │
│   ├─ Realtime (WebSockets)                             │
│   └─ Edge Functions (Deno)                             │
│                                                         │
└─────────────────────────────────────────────────────────┘
                           ↑
                           │ (HTTPS/PostgreSQL)
                           │
┌──────────────────────────┴──────────────────────────────┐
│ Your Infrastructure (DigitalOcean/Local)               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ n8n (https://n8n.insightpulseai.net)                   │
│ Odoo CE 18 (SGP1 droplet)                              │
│ Apache Superset (superset.insightpulseai.net)          │
│ OCR Service (SGP1 droplet)                             │
│ MCP Coordinator (mcp.insightpulseai.net)               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Connection Details

### Environment Variables Required

All services need these Supabase credentials:

```bash
# Supabase Project
SUPABASE_PROJECT_REF=xkxyvboeubffxxbebsll
SUPABASE_URL=https://xkxyvboeubffxxbebsll.supabase.co

# API Keys
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # Client-side
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # Server-side

# PostgreSQL Direct Connection (for migrations, psql, etc.)
DATABASE_URL=postgresql://postgres:[PASSWORD]@aws-1-us-east-1.pooler.supabase.com:6543/postgres

# Alternative: Direct connection (no pooler)
POSTGRES_URL=postgresql://postgres:[PASSWORD]@aws-1-us-east-1.compute.aws.supabase.com:5432/postgres
```

### When to Use Which Connection

| Use Case | Connection Type | Port | Why |
|----------|----------------|------|-----|
| **Migrations** (Supabase CLI) | Direct | 5432 | Schema changes need direct access |
| **App runtime** (Odoo, n8n) | Pooler | 6543 | Connection pooling for efficiency |
| **CLI tools** (psql, pg_dump) | Direct | 5432 | Admin operations |
| **Edge Functions** | PostgREST API | HTTPS | Serverless, no connection pooling |

---

## Database Schema Management

### **DO NOT** use docker-entrypoint-initdb.d

Since Supabase is external, you cannot use Docker init scripts.

### **DO** use Supabase CLI

```bash
# Initialize Supabase locally (for migration management)
supabase init

# Link to your project
supabase link --project-ref xkxyvboeubffxxbebsll

# Create migrations
supabase migration new <migration_name>

# Push migrations to Supabase
supabase db push

# Or use raw SQL
psql "$DATABASE_URL" -f migrations/001_initial_schema.sql
```

### Example Migration Workflow

```bash
# 1. Create migration file
cat > supabase/migrations/$(date +%Y%m%d%H%M%S)_task_queue.sql << 'EOF'
-- Task Queue for Docs2Code Pipeline
CREATE TABLE IF NOT EXISTS task_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  kind TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  payload JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS policies
ALTER TABLE task_queue ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access" ON task_queue
  FOR ALL USING (auth.role() = 'service_role');
EOF

# 2. Apply migration
supabase db push

# Or manually:
psql "$DATABASE_URL" -f supabase/migrations/$(ls -t supabase/migrations | head -1)
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy Database Migrations

on:
  push:
    paths:
      - 'supabase/migrations/**'

jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Supabase CLI
        uses: supabase/setup-cli@v1

      - name: Run migrations
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
          SUPABASE_PROJECT_REF: xkxyvboeubffxxbebsll
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          supabase link --project-ref $SUPABASE_PROJECT_REF
          supabase db push
```

---

## Service Integration Patterns

### n8n → Supabase

**Use PostgREST API (recommended)**:

```javascript
// n8n HTTP Request node
{
  "method": "POST",
  "url": "https://xkxyvboeubffxxbebsll.supabase.co/rest/v1/task_queue",
  "headers": {
    "apikey": "{{$env.SUPABASE_ANON_KEY}}",
    "Authorization": "Bearer {{$env.SUPABASE_SERVICE_ROLE_KEY}}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
  },
  "body": {
    "kind": "docs_sync",
    "payload": {"doc_id": "..."}
  }
}
```

**Alternative: Direct PostgreSQL** (if using Supabase node):

```javascript
// n8n Postgres node
{
  "host": "aws-1-us-east-1.pooler.supabase.com",
  "port": 6543,
  "database": "postgres",
  "user": "postgres",
  "password": "{{$env.SUPABASE_DB_PASSWORD}}",
  "ssl": true
}
```

### Odoo → Supabase

**Python (psycopg2 with pooler)**:

```python
import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool

DATABASE_URL = os.environ['DATABASE_URL']

# Connection pool (recommended for Odoo)
pool = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=DATABASE_URL
)

conn = pool.getconn()
cursor = conn.cursor()

# Use Supabase-specific functions
cursor.execute("""
    SELECT * FROM task_queue
    WHERE status = 'pending'
    ORDER BY created_at ASC
    LIMIT 10
""")

results = cursor.fetchall()
pool.putconn(conn)
```

### Apache Superset → Supabase

**Database connection string** (in Superset UI):

```
postgresql://postgres:[PASSWORD]@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require
```

---

## Security Best Practices

### RLS (Row-Level Security)

**Always enable RLS** on public tables:

```sql
-- Enable RLS
ALTER TABLE your_table ENABLE ROW LEVEL SECURITY;

-- Policy for service role (full access)
CREATE POLICY "Service role full access" ON your_table
  FOR ALL
  USING (auth.role() = 'service_role');

-- Policy for authenticated users (limited access)
CREATE POLICY "Users can read own data" ON your_table
  FOR SELECT
  USING (auth.uid() = user_id);
```

### API Key Usage

| Key Type | Use For | Expose? |
|----------|---------|---------|
| `SUPABASE_ANON_KEY` | Client-side apps, browser | ✅ Safe to expose |
| `SUPABASE_SERVICE_ROLE_KEY` | Server-side, backend, n8n | ❌ NEVER expose |

### Storage Locations

```bash
# GitHub Secrets (for CI/CD)
SUPABASE_ACCESS_TOKEN=sbp_...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
DATABASE_URL=postgresql://...

# Supabase Vault (for Edge Functions)
# Store secrets in: Supabase Dashboard → Project Settings → Vault
# Access in Edge Functions: Deno.env.get("SECRET_NAME")

# Local .env (for development, gitignored)
SUPABASE_URL=https://xkxyvboeubffxxbebsll.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...
DATABASE_URL=...
```

---

## Troubleshooting

### "Connection refused" (Port 5432)

**Cause**: Trying to connect directly without SSL or from blocked IP

**Fix**:
```bash
# Always use pooler for app connections
DATABASE_URL="postgresql://postgres:PASSWORD@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"

# Or add your IP to Supabase allowlist
# Dashboard → Settings → Database → Connection Pooling → IP Allowlist
```

### "Too many connections"

**Cause**: Direct connections without pooler

**Fix**: Always use port 6543 (Supavisor pooler) for app runtime

### "RLS policy violation"

**Cause**: Missing or incorrect RLS policies

**Fix**:
```sql
-- Check current policies
SELECT * FROM pg_policies WHERE tablename = 'your_table';

-- Grant service role access
CREATE POLICY "Service role bypass" ON your_table
  FOR ALL USING (auth.role() = 'service_role');
```

---

## Migration Checklist

**DO NOT** create local Postgres containers for Supabase.

**✅ DO:**
1. Use `SUPABASE_URL` and API keys in all apps
2. Use pooler (port 6543) for runtime connections
3. Use Supabase CLI for migrations
4. Store credentials in GitHub Secrets / Supabase Vault
5. Enable RLS on all public tables

**❌ DON'T:**
1. Create docker-compose services for Supabase
2. Try to self-host Supabase (it's managed)
3. Use direct connection (5432) for app runtime
4. Expose `SERVICE_ROLE_KEY` in client code
5. Skip RLS policies

---

## Quick Reference

### Connection Strings

```bash
# Pooler (for apps)
postgresql://postgres:[PASSWORD]@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require

# Direct (for migrations/admin)
postgresql://postgres:[PASSWORD]@aws-1-us-east-1.compute.aws.supabase.com:5432/postgres?sslmode=require

# PostgREST API
https://xkxyvboeubffxxbebsll.supabase.co/rest/v1/

# Realtime
wss://xkxyvboeubffxxbebsll.supabase.co/realtime/v1/
```

### Useful Commands

```bash
# Test connection
psql "$DATABASE_URL" -c "SELECT NOW();"

# List tables
psql "$DATABASE_URL" -c "\dt"

# Run migration
psql "$DATABASE_URL" -f migrations/001_schema.sql

# Supabase CLI
supabase db diff    # Show schema changes
supabase db push    # Apply migrations
supabase db reset   # Reset local dev DB (safe, doesn't touch production)
```

---

**Last Updated**: 2026-01-01
**Supabase Project**: xkxyvboeubffxxbebsll
**Region**: AWS US-East-1
