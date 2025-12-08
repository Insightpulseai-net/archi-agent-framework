# Data Engineering Workbench - Monitoring Guide

## Overview

This document describes the monitoring strategy for the Data Engineering Workbench, including metrics to track, alerting rules, and dashboard configurations.

---

## 1. Metrics Collection

### 1.1 Infrastructure Metrics

| Metric | Description | Source | Alert Threshold |
|--------|-------------|--------|-----------------|
| `cpu_usage_percent` | Container CPU utilization | Docker stats | > 80% for 5m |
| `memory_usage_bytes` | Container memory usage | Docker stats | > 85% of limit |
| `disk_usage_percent` | Volume disk utilization | df | > 80% |
| `network_rx_bytes` | Network bytes received | Docker stats | Anomaly detection |
| `network_tx_bytes` | Network bytes transmitted | Docker stats | Anomaly detection |

### 1.2 Application Metrics

| Metric | Description | Labels | Alert Threshold |
|--------|-------------|--------|-----------------|
| `workbench_http_requests_total` | Total HTTP requests | method, path, status | Error rate > 5% |
| `workbench_http_request_duration_seconds` | Request latency | method, path | P95 > 5s |
| `workbench_notebook_executions_total` | Notebook cell executions | kernel_type, status | Error rate > 10% |
| `workbench_query_duration_seconds` | Query execution time | connection_type | P95 > 30s |
| `workbench_pipeline_runs_total` | Pipeline executions | pipeline_name, status | Failure rate > 5% |
| `workbench_active_sessions` | Active user sessions | - | > 50 |
| `workbench_connection_pool_size` | Database connections | database | > 80% of max |

### 1.3 External Service Metrics

| Metric | Description | Service | Alert Threshold |
|--------|-------------|---------|-----------------|
| `odoo_api_latency_seconds` | Odoo API response time | Odoo | > 5s |
| `superset_api_latency_seconds` | Superset API response time | Superset | > 3s |
| `ocr_processing_time_seconds` | OCR processing duration | OCR Service | > 30s |
| `agent_task_duration_seconds` | Agent task completion time | MCP Agents | > 120s |

---

## 2. Prometheus Configuration

### 2.1 Scrape Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'workbench-api'
    static_configs:
      - targets: ['workbench-api:8000']
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - '/etc/prometheus/rules/*.yml'
```

### 2.2 Alert Rules

```yaml
# /etc/prometheus/rules/workbench.yml
groups:
  - name: workbench
    rules:
      # High Error Rate
      - alert: HighErrorRate
        expr: |
          sum(rate(workbench_http_requests_total{status=~"5.."}[5m]))
          / sum(rate(workbench_http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      # Slow Queries
      - alert: SlowQueries
        expr: |
          histogram_quantile(0.95,
            rate(workbench_query_duration_seconds_bucket[5m])
          ) > 30
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow query execution detected"
          description: "P95 query latency is {{ $value }}s"

      # Pipeline Failures
      - alert: PipelineFailures
        expr: |
          sum(rate(workbench_pipeline_runs_total{status="failed"}[1h]))
          / sum(rate(workbench_pipeline_runs_total[1h])) > 0.1
        for: 15m
        labels:
          severity: critical
        annotations:
          summary: "High pipeline failure rate"
          description: "{{ $value | humanizePercentage }} of pipelines are failing"

      # Database Connection Pool Exhaustion
      - alert: DatabaseConnectionPoolExhausted
        expr: workbench_connection_pool_size / workbench_connection_pool_max > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database connection pool near capacity"
          description: "Connection pool is {{ $value | humanizePercentage }} full"

      # High Memory Usage
      - alert: HighMemoryUsage
        expr: |
          container_memory_usage_bytes{name=~"workbench.*"}
          / container_spec_memory_limit_bytes > 0.85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.name }}"
          description: "Memory usage is {{ $value | humanizePercentage }}"

      # Service Down
      - alert: ServiceDown
        expr: up{job=~"workbench.*"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
          description: "Service has been unreachable for more than 2 minutes"
```

---

## 3. Grafana Dashboards

### 3.1 Workbench Overview Dashboard

**Panels**:
1. **Request Rate** - Requests per second by endpoint
2. **Error Rate** - 5xx errors as percentage
3. **Latency Distribution** - P50, P95, P99 latencies
4. **Active Users** - Current session count
5. **Pipeline Status** - Running, completed, failed counts
6. **Resource Usage** - CPU, memory, disk gauges

**Dashboard JSON**: Import from `grafana/dashboards/workbench-overview.json`

### 3.2 Pipeline Monitoring Dashboard

**Panels**:
1. **Pipeline Runs by Status** - Stacked bar chart
2. **Pipeline Duration Trends** - Time series
3. **Task-Level Status** - Heatmap
4. **Error Messages** - Log panel
5. **SLA Compliance** - Gauge showing % within SLA

### 3.3 Database Performance Dashboard

**Panels**:
1. **Query Throughput** - Queries per second
2. **Query Latency** - By query type
3. **Connection Pool** - Active vs available
4. **Table Sizes** - Top tables by size
5. **Index Hit Ratio** - Cache effectiveness

---

## 4. DigitalOcean Monitoring Integration

### 4.1 Droplet Metrics (Built-in)

Navigate to DigitalOcean Console → Monitoring:
- CPU utilization
- Memory usage
- Disk I/O
- Network bandwidth

### 4.2 Alerts Configuration

Set up DO alerts for:
```
CPU > 80% for 5 minutes
Memory > 85% for 5 minutes
Disk > 80%
```

### 4.3 Uptime Checks

Create HTTP checks:
- **Workbench API**: `https://workbench.insightpulseai.net/health`
- **n8n**: `https://n8n.insightpulseai.net/`
- **Check interval**: 1 minute
- **Alert threshold**: 2 consecutive failures

---

## 5. Superset Integration (Self-Monitoring)

Use the workbench's own Superset integration to visualize operational data:

### 5.1 Create Monitoring Dataset

```sql
-- ops_metrics view
CREATE VIEW gold.ops_metrics AS
SELECT
    date_trunc('hour', created_at) as hour,
    count(*) as pipeline_runs,
    count(*) filter (where status = 'completed') as successful,
    count(*) filter (where status = 'failed') as failed,
    avg(duration_ms) as avg_duration_ms,
    percentile_cont(0.95) within group (order by duration_ms) as p95_duration_ms
FROM workbench.pipeline_runs
WHERE created_at >= now() - interval '7 days'
GROUP BY 1;
```

### 5.2 Dashboard Queries

**Pipeline Success Rate**:
```sql
SELECT
    hour,
    successful::float / nullif(pipeline_runs, 0) * 100 as success_rate
FROM gold.ops_metrics
ORDER BY hour;
```

---

## 6. Log Aggregation

### 6.1 Structured Logging Format

All services use JSON structured logs:
```json
{
    "timestamp": "2025-01-15T10:30:00Z",
    "level": "INFO",
    "logger": "workbench.api",
    "message": "Request completed",
    "request_id": "abc123",
    "method": "POST",
    "path": "/api/v1/execute/sql",
    "status_code": 200,
    "duration_ms": 150,
    "user_id": "user-uuid"
}
```

### 6.2 Log Locations

| Service | Log Location |
|---------|--------------|
| API | `/var/log/workbench/api.log` |
| Nginx | `/var/log/nginx/workbench_*.log` |
| Postgres | Docker logs |
| n8n | Docker logs |

### 6.3 Log Queries (via grep/jq)

```bash
# Find errors in last hour
docker logs workbench-api --since 1h 2>&1 | grep '"level":"ERROR"' | jq .

# Find slow requests
docker logs workbench-api --since 1h 2>&1 | jq 'select(.duration_ms > 5000)'

# Count requests by status
docker logs workbench-api --since 1h 2>&1 | jq -r '.status_code' | sort | uniq -c
```

---

## 7. Alert Routing

### 7.1 Severity Levels

| Severity | Response Time | Notification |
|----------|---------------|--------------|
| Critical | 15 minutes | Slack + PagerDuty |
| Warning | 1 hour | Slack |
| Info | 4 hours | Email digest |

### 7.2 Alert Channels

```yaml
# alertmanager.yml
route:
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty-critical'
    - match:
        severity: warning
      receiver: 'slack-warnings'

receivers:
  - name: 'default'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#data-engineering-alerts'

  - name: 'slack-warnings'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#data-engineering-alerts'

  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: '${PAGERDUTY_KEY}'
```

---

## 8. Health Check Endpoints

### 8.1 Workbench API

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `/health` | Basic health | `{"status": "healthy"}` |
| `/ready` | Full readiness | `{"status": "ready", "checks": {...}}` |
| `/metrics` | Prometheus metrics | Prometheus format |

### 8.2 Sample Health Check Script

```bash
#!/bin/bash
# check-health.sh

WORKBENCH_URL="${WORKBENCH_URL:-https://workbench.insightpulseai.net}"

check_endpoint() {
    local name=$1
    local url=$2
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$url")

    if [ "$response" = "200" ]; then
        echo "✓ $name: OK"
        return 0
    else
        echo "✗ $name: FAILED (HTTP $response)"
        return 1
    fi
}

echo "Health Check - $(date)"
echo "========================"

check_endpoint "Workbench API" "$WORKBENCH_URL/health"
check_endpoint "Workbench Ready" "$WORKBENCH_URL/ready"
check_endpoint "n8n" "https://n8n.insightpulseai.net/"

echo "========================"
```

---

## 9. Capacity Planning

### 9.1 Key Metrics for Scaling

| Metric | Scale-Up Threshold | Action |
|--------|-------------------|--------|
| CPU sustained > 70% | 1 week | Upgrade droplet |
| Memory sustained > 80% | 1 week | Upgrade droplet |
| Disk > 70% | 1 month | Expand volume |
| Request latency P95 > 3s | 1 week | Optimize or scale |
| Concurrent users > 80% capacity | 1 month | Add capacity |

### 9.2 Growth Projections

Track monthly:
- Pipeline run volume
- Data storage growth
- User count
- API request volume

---

## 10. Runbook References

For incident response procedures, see:
- [Workbench Outage Runbook](./runbook-workbench-outage.md)
- [Backup & Recovery](./backups.md)
