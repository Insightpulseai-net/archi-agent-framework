# Runbook: Data Engineering Workbench Outage

## Document Info
- **Last Updated**: 2025-12-08
- **Owner**: Platform Team
- **Severity Classification**: P1 (Critical)
- **Expected Resolution Time**: < 1 hour

---

## 1. Quick Reference

### 1.1 Key URLs

| Service | URL | Health Check |
|---------|-----|--------------|
| Workbench UI | https://workbench.insightpulseai.net | `/health` |
| Workbench API | https://workbench.insightpulseai.net/api | `/api/v1/health` |
| n8n | https://n8n.insightpulseai.net | `/` |
| Temporal UI | https://workbench.insightpulseai.net/temporal | `/` |

### 1.2 SSH Access

```bash
ssh root@159.223.75.148  # If co-located with Odoo
# or
ssh root@WORKBENCH_DROPLET_IP  # If dedicated droplet
```

### 1.3 Key Contacts

| Role | Contact |
|------|---------|
| On-Call Engineer | #data-engineering Slack |
| Infrastructure | #devops Slack |
| Security Escalation | security@insightpulseai.net |

---

## 2. Triage Steps

### 2.1 Initial Assessment (< 5 minutes)

```bash
# 1. Check if site is reachable
curl -I https://workbench.insightpulseai.net/health

# 2. SSH to server
ssh root@WORKBENCH_IP

# 3. Check Docker status
docker ps -a | grep workbench

# 4. Check system resources
htop  # or top
df -h
free -m

# 5. Check recent logs
docker logs workbench-api --tail 100 --since 10m
docker logs workbench-frontend --tail 100 --since 10m
```

### 2.2 Determine Outage Type

| Symptom | Likely Cause | Go To Section |
|---------|--------------|---------------|
| 502/503 errors | Container crash | Section 3.1 |
| Connection timeout | Network/firewall | Section 3.2 |
| SSL errors | Certificate issue | Section 3.3 |
| 500 errors | Application error | Section 3.4 |
| Slow responses | Resource exhaustion | Section 3.5 |
| Database errors | PostgreSQL issue | Section 3.6 |

---

## 3. Resolution Procedures

### 3.1 Container Crash

**Symptoms**: 502 Bad Gateway, containers not running

**Steps**:
```bash
# 1. Check container status
docker ps -a | grep workbench

# 2. Check exit codes and logs
docker logs workbench-api --tail 200

# 3. Check for OOM kills
dmesg | grep -i "out of memory" | tail -20

# 4. Restart containers
cd /opt/workbench/infra
docker compose -f docker-compose.workbench.yml restart

# 5. If restart fails, check disk space
df -h
docker system df

# 6. Clean up if needed
docker system prune -f  # Careful: removes unused data

# 7. Bring up fresh
docker compose -f docker-compose.workbench.yml down
docker compose -f docker-compose.workbench.yml up -d
```

**Verification**:
```bash
curl https://workbench.insightpulseai.net/health
docker ps | grep workbench  # All containers should be "Up"
```

---

### 3.2 Network/Firewall Issues

**Symptoms**: Connection timeout, no response

**Steps**:
```bash
# 1. Check if nginx is running
systemctl status nginx

# 2. Check firewall rules
ufw status verbose

# 3. Verify ports are listening
netstat -tlnp | grep -E '80|443|8000|3000'
# or
ss -tlnp | grep -E '80|443|8000|3000'

# 4. Check nginx config
nginx -t

# 5. Check DigitalOcean firewall (via console or doctl)
doctl compute firewall list

# 6. Test internal connectivity
curl http://localhost:8000/health
curl http://localhost:3000/

# 7. Restart nginx if needed
systemctl restart nginx
```

**Verification**:
```bash
# From external machine
curl -I https://workbench.insightpulseai.net
```

---

### 3.3 SSL Certificate Issues

**Symptoms**: SSL errors, certificate warnings

**Steps**:
```bash
# 1. Check certificate expiry
echo | openssl s_client -connect workbench.insightpulseai.net:443 2>/dev/null | openssl x509 -noout -dates

# 2. Check certbot status
certbot certificates

# 3. If expired, renew
certbot renew --force-renewal

# 4. If certbot fails, check DNS
dig workbench.insightpulseai.net

# 5. Manual certificate renewal
certbot --nginx -d workbench.insightpulseai.net

# 6. Reload nginx
nginx -t && systemctl reload nginx
```

**Verification**:
```bash
curl -vI https://workbench.insightpulseai.net 2>&1 | grep -E "SSL|certificate"
```

---

### 3.4 Application Errors (500)

**Symptoms**: 500 Internal Server Error

**Steps**:
```bash
# 1. Check API logs for errors
docker logs workbench-api --tail 500 2>&1 | grep -i error

# 2. Check for specific error patterns
docker logs workbench-api --tail 500 2>&1 | grep -E "Traceback|Exception|Error"

# 3. Check environment variables
docker exec workbench-api env | grep -v KEY | grep -v SECRET

# 4. Test database connection
docker exec workbench-api python -c "from app.core.database import check_db_connection; import asyncio; print(asyncio.run(check_db_connection()))"

# 5. Test Redis connection
docker exec workbench-api python -c "from app.core.redis import check_redis_connection; import asyncio; print(asyncio.run(check_redis_connection()))"

# 6. If dependency issue, restart specific service
docker compose -f docker-compose.workbench.yml restart workbench-api
```

**Common Issues**:
- Missing environment variable → Check `.env.workbench`
- Database migration needed → Run migrations
- Package issue → Rebuild container

---

### 3.5 Resource Exhaustion

**Symptoms**: Slow responses, timeouts, OOM

**Steps**:
```bash
# 1. Check system resources
htop
free -m
df -h

# 2. Check container resource usage
docker stats --no-stream

# 3. Identify memory hogs
ps aux --sort=-%mem | head -20

# 4. Check for runaway processes
top -b -n 1 | head -20

# 5. If disk full, clean up
docker system prune -f
journalctl --vacuum-time=7d
find /var/log -name "*.log" -mtime +7 -delete

# 6. If memory issue, restart heavy containers
docker compose -f docker-compose.workbench.yml restart jupyter-server temporal-server

# 7. If persistent, consider scaling
# - Upgrade droplet
# - Add swap (temporary)
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```

---

### 3.6 Database Issues

**Symptoms**: Database connection errors, query failures

**Steps**:
```bash
# 1. Check PostgreSQL container
docker logs workbench-postgres --tail 100

# 2. Check if PostgreSQL is accepting connections
docker exec workbench-postgres pg_isready -U workbench

# 3. Check connection count
docker exec workbench-postgres psql -U workbench -c "SELECT count(*) FROM pg_stat_activity;"

# 4. Check for locks
docker exec workbench-postgres psql -U workbench -c "SELECT * FROM pg_locks WHERE NOT granted;"

# 5. Check disk space for database
docker exec workbench-postgres psql -U workbench -c "SELECT pg_size_pretty(pg_database_size('workbench'));"

# 6. If connection pool exhausted, restart API
docker compose -f docker-compose.workbench.yml restart workbench-api

# 7. If PostgreSQL crashed, check for corruption
docker exec workbench-postgres psql -U workbench -c "ANALYZE VERBOSE;"

# 8. Recovery from backup if needed (see backups.md)
```

---

## 4. Rollback Procedures

### 4.1 Rollback Application Code

```bash
# If recent deployment caused issue
cd /opt/workbench

# Check recent commits
git log --oneline -10

# Rollback to previous version
git checkout <previous-commit-hash>

# Rebuild and restart
docker compose -f infra/docker-compose.workbench.yml build
docker compose -f infra/docker-compose.workbench.yml up -d
```

### 4.2 Rollback Database Migration

```bash
# Check current migration state
docker exec workbench-api alembic current

# Downgrade one revision
docker exec workbench-api alembic downgrade -1

# Or downgrade to specific revision
docker exec workbench-api alembic downgrade <revision_id>
```

### 4.3 Rollback Configuration

```bash
# Restore from config backup
tar -xzf /opt/workbench/backups/config/config_YYYYMMDD.tar.gz -C /

# Restart services
docker compose -f docker-compose.workbench.yml down
docker compose -f docker-compose.workbench.yml up -d
```

---

## 5. Post-Incident Steps

### 5.1 Immediate (Within 1 hour of resolution)

- [ ] Verify all services are healthy
- [ ] Check monitoring dashboards
- [ ] Notify stakeholders of resolution
- [ ] Document timeline in incident channel

### 5.2 Same Day

- [ ] Review logs for root cause
- [ ] Check for related issues
- [ ] Update monitoring/alerts if gaps found
- [ ] Brief write-up in incident tracker

### 5.3 Within 48 Hours

- [ ] Complete post-mortem document
- [ ] Identify action items
- [ ] Schedule follow-up work
- [ ] Update runbooks if needed

---

## 6. Escalation Matrix

| Duration | Action |
|----------|--------|
| 0-15 min | On-call engineer diagnoses |
| 15-30 min | Escalate to secondary on-call |
| 30-60 min | Escalate to team lead |
| 60+ min | Escalate to management |

### Escalation Contacts

```
Primary:    #data-engineering Slack
Secondary:  @devops-oncall Slack
Team Lead:  Email + Phone
Management: Email + Phone (for P1 > 1hr)
```

---

## 7. Preventive Measures

### 7.1 Daily Checks

- [ ] Review alert dashboard
- [ ] Check backup completion
- [ ] Review error log summary

### 7.2 Weekly Checks

- [ ] Review resource utilization trends
- [ ] Check certificate expiry (< 30 days warning)
- [ ] Verify backup restore capability

### 7.3 Monthly Checks

- [ ] Test full recovery procedure
- [ ] Review and update runbooks
- [ ] Capacity planning review

---

## Appendix A: Common Commands

```bash
# Service status
docker compose -f docker-compose.workbench.yml ps

# View all logs
docker compose -f docker-compose.workbench.yml logs -f

# Restart all services
docker compose -f docker-compose.workbench.yml restart

# Full restart
docker compose -f docker-compose.workbench.yml down && docker compose -f docker-compose.workbench.yml up -d

# Force rebuild
docker compose -f docker-compose.workbench.yml build --no-cache
docker compose -f docker-compose.workbench.yml up -d

# Enter container shell
docker exec -it workbench-api bash
docker exec -it workbench-postgres psql -U workbench
docker exec -it workbench-redis redis-cli
```

---

## Appendix B: Log Locations

| Service | Container Logs | File Logs |
|---------|----------------|-----------|
| API | `docker logs workbench-api` | `/var/log/workbench/api.log` |
| Frontend | `docker logs workbench-frontend` | N/A |
| PostgreSQL | `docker logs workbench-postgres` | `/var/lib/postgresql/data/log/` |
| nginx | `docker logs workbench-nginx` | `/var/log/nginx/` |
| n8n | `docker logs n8n` | N/A |
