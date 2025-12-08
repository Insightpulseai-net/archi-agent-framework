# Data Engineering Workbench - Backup & Recovery Guide

## Overview

This document describes the backup strategy, procedures, and recovery processes for the Data Engineering Workbench.

---

## 1. Backup Strategy

### 1.1 What Gets Backed Up

| Component | Data | Frequency | Retention |
|-----------|------|-----------|-----------|
| PostgreSQL | All schemas (workbench, bronze, silver, gold, audit) | Hourly | 24h (hourly), 30d (daily), 90d (weekly) |
| MinIO/S3 | Documents, notebooks, uploads | Daily | 30 days |
| Configuration | .env files, nginx config | Daily | 90 days |
| Docker Volumes | notebooks, uploads | Daily | 30 days |
| n8n | Workflows, credentials | Daily | 30 days |

### 1.2 Backup Schedule

```
Hourly:   Database (pg_dump) → local
Daily:    Database + Files + Config → local + remote (optional)
Weekly:   Full backup → archive
Monthly:  Full backup → long-term archive
```

### 1.3 RPO/RTO Targets

| Tier | RPO (Max Data Loss) | RTO (Recovery Time) | Applicable To |
|------|---------------------|---------------------|---------------|
| Critical | 15 minutes | 1 hour | Production database |
| Standard | 24 hours | 4 hours | Files, configuration |
| Archive | 7 days | 24 hours | Historical data |

---

## 2. Backup Procedures

### 2.1 Automated Backups

The backup script (`/opt/workbench/infra/scripts/backup.sh`) runs automatically via cron:

```bash
# Crontab entry (added by setup script)
0 * * * * /opt/workbench/infra/scripts/backup.sh db >> /var/log/workbench-backup.log 2>&1
0 2 * * * /opt/workbench/infra/scripts/backup.sh full >> /var/log/workbench-backup.log 2>&1
```

### 2.2 Manual Database Backup

```bash
# SSH to workbench droplet
ssh root@workbench.insightpulseai.net

# Full database dump
docker exec workbench-postgres pg_dump \
    -U workbench \
    -d workbench \
    --no-owner \
    --no-acl \
    > /opt/workbench/backups/manual/db_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
docker exec workbench-postgres pg_dump \
    -U workbench \
    -d workbench \
    --no-owner \
    --no-acl \
    | gzip > /opt/workbench/backups/manual/db_$(date +%Y%m%d_%H%M%S).sql.gz

# Schema-specific backup (e.g., bronze layer only)
docker exec workbench-postgres pg_dump \
    -U workbench \
    -d workbench \
    --schema=bronze \
    > /opt/workbench/backups/manual/bronze_$(date +%Y%m%d_%H%M%S).sql
```

### 2.3 Docker Volume Backup

```bash
# Backup notebooks volume
docker run --rm \
    -v workbench-notebooks:/source:ro \
    -v /opt/workbench/backups:/backup \
    alpine tar -czf /backup/notebooks_$(date +%Y%m%d).tar.gz -C /source .

# Backup uploads volume
docker run --rm \
    -v workbench-uploads:/source:ro \
    -v /opt/workbench/backups:/backup \
    alpine tar -czf /backup/uploads_$(date +%Y%m%d).tar.gz -C /source .
```

### 2.4 MinIO/S3 Backup

```bash
# Using mc (MinIO Client)
mc alias set workbench http://localhost:9000 $MINIO_ACCESS_KEY $MINIO_SECRET_KEY

# Mirror to local backup
mc mirror workbench/workbench-data /opt/workbench/backups/minio/

# Mirror to external S3 (if configured)
mc mirror workbench/workbench-data s3backup/workbench-backup/$(date +%Y%m%d)/
```

### 2.5 n8n Workflow Backup

```bash
# Export all workflows via API
curl -X GET "http://localhost:5678/api/v1/workflows" \
    -H "X-N8N-API-KEY: $N8N_API_KEY" \
    | jq '.' > /opt/workbench/backups/n8n/workflows_$(date +%Y%m%d).json

# Export credentials (encrypted)
docker exec n8n n8n export:credentials \
    --all \
    --output=/data/backup/credentials_$(date +%Y%m%d).json
```

### 2.6 Configuration Backup

```bash
# Backup all config files
tar -czf /opt/workbench/backups/config/config_$(date +%Y%m%d).tar.gz \
    /opt/workbench/infra/.env.workbench \
    /opt/workbench/infra/nginx/ \
    /opt/workbench/infra/docker-compose.workbench.yml \
    /etc/nginx/sites-available/ \
    /etc/letsencrypt/
```

---

## 3. Encryption

### 3.1 Encrypting Backups

All backups should be encrypted before offsite storage:

```bash
# Encrypt with symmetric key
openssl enc -aes-256-cbc -salt -pbkdf2 \
    -in backup.sql.gz \
    -out backup.sql.gz.enc \
    -pass pass:"$BACKUP_ENCRYPTION_KEY"

# Decrypt
openssl enc -d -aes-256-cbc -pbkdf2 \
    -in backup.sql.gz.enc \
    -out backup.sql.gz \
    -pass pass:"$BACKUP_ENCRYPTION_KEY"
```

### 3.2 Key Management

- Encryption key stored in `.env.workbench` as `BACKUP_ENCRYPTION_KEY`
- Key should be at least 32 characters (256 bits)
- Store a copy of the key securely offline (password manager, vault)
- Rotate key annually

---

## 4. Remote Backup (Optional)

### 4.1 DigitalOcean Spaces

```bash
# Configure s3cmd
cat > ~/.s3cfg << EOF
[default]
access_key = $DO_SPACES_ACCESS_KEY
secret_key = $DO_SPACES_SECRET_KEY
host_base = nyc3.digitaloceanspaces.com
host_bucket = %(bucket)s.nyc3.digitaloceanspaces.com
EOF

# Upload encrypted backup
s3cmd put /opt/workbench/backups/daily/*.enc \
    s3://workbench-backups/$(date +%Y/%m/%d)/
```

### 4.2 AWS S3 (Cross-Region)

```bash
# Configure AWS CLI
aws configure set aws_access_key_id $AWS_ACCESS_KEY
aws configure set aws_secret_access_key $AWS_SECRET_KEY

# Sync backups to S3
aws s3 sync /opt/workbench/backups/daily/ \
    s3://insightpulseai-backups/workbench/$(date +%Y/%m/%d)/ \
    --storage-class STANDARD_IA
```

---

## 5. Recovery Procedures

### 5.1 Database Recovery

#### Full Database Restore

```bash
# Stop application containers
cd /opt/workbench/infra
docker compose -f docker-compose.workbench.yml stop workbench-api workbench-frontend

# Restore from backup
docker exec -i workbench-postgres psql -U workbench -d postgres << EOF
DROP DATABASE IF EXISTS workbench;
CREATE DATABASE workbench;
EOF

# Decrypt if encrypted
openssl enc -d -aes-256-cbc -pbkdf2 \
    -in /opt/workbench/backups/daily/db_20250115.sql.gz.enc \
    -pass pass:"$BACKUP_ENCRYPTION_KEY" \
    | gunzip \
    | docker exec -i workbench-postgres psql -U workbench -d workbench

# Restart services
docker compose -f docker-compose.workbench.yml up -d
```

#### Point-in-Time Recovery (if WAL archiving enabled)

```bash
# Restore base backup
docker exec -i workbench-postgres pg_restore \
    -U workbench \
    -d workbench \
    /var/lib/postgresql/data/backup/base.tar

# Apply WAL logs up to specific time
docker exec workbench-postgres pg_ctl \
    -D /var/lib/postgresql/data \
    -o "-c recovery_target_time='2025-01-15 14:30:00'" \
    start
```

### 5.2 Volume Recovery

```bash
# Stop containers
docker compose -f docker-compose.workbench.yml down

# Remove old volume
docker volume rm workbench-notebooks

# Create new volume
docker volume create workbench-notebooks

# Restore from backup
docker run --rm \
    -v workbench-notebooks:/target \
    -v /opt/workbench/backups:/backup:ro \
    alpine tar -xzf /backup/notebooks_20250115.tar.gz -C /target

# Restart
docker compose -f docker-compose.workbench.yml up -d
```

### 5.3 MinIO Recovery

```bash
# Stop MinIO
docker compose stop minio

# Clear existing data
docker volume rm minio-data
docker volume create minio-data

# Restore from backup
docker run --rm \
    -v minio-data:/data \
    -v /opt/workbench/backups/minio:/backup:ro \
    alpine sh -c "cp -r /backup/* /data/"

# Restart
docker compose up -d minio
```

### 5.4 n8n Recovery

```bash
# Import workflows
curl -X POST "http://localhost:5678/api/v1/workflows" \
    -H "X-N8N-API-KEY: $N8N_API_KEY" \
    -H "Content-Type: application/json" \
    -d @/opt/workbench/backups/n8n/workflows_20250115.json

# Import credentials (requires re-entering secrets)
docker exec n8n n8n import:credentials \
    --input=/data/backup/credentials_20250115.json
```

### 5.5 Full System Recovery

For complete system recovery (new droplet):

```bash
# 1. Provision new droplet
# 2. Run setup script
curl -fsSL https://raw.githubusercontent.com/your-org/fin-workspace-automation/main/infra/scripts/setup-workbench-droplet.sh | bash

# 3. Restore configuration
tar -xzf config_backup.tar.gz -C /

# 4. Update .env.workbench with correct values
nano /opt/workbench/infra/.env.workbench

# 5. Restore database
# (Follow Database Recovery steps above)

# 6. Restore volumes
# (Follow Volume Recovery steps above)

# 7. Update DNS if IP changed
# Update Squarespace DNS: workbench.insightpulseai.net → NEW_IP

# 8. Renew SSL certificates
certbot --nginx -d workbench.insightpulseai.net

# 9. Start services
docker compose -f docker-compose.workbench.yml up -d

# 10. Verify
curl https://workbench.insightpulseai.net/health
```

---

## 6. Verification

### 6.1 Backup Verification Script

```bash
#!/bin/bash
# verify-backup.sh

BACKUP_DIR="/opt/workbench/backups/daily"
LATEST_DB=$(ls -t $BACKUP_DIR/db_*.sql.gz* 2>/dev/null | head -1)

echo "Verifying latest backup: $LATEST_DB"

# Check file exists and has size
if [ ! -f "$LATEST_DB" ]; then
    echo "ERROR: No backup file found"
    exit 1
fi

SIZE=$(stat -f%z "$LATEST_DB" 2>/dev/null || stat -c%s "$LATEST_DB")
if [ "$SIZE" -lt 1000 ]; then
    echo "ERROR: Backup file too small ($SIZE bytes)"
    exit 1
fi

# Test decryption (if encrypted)
if [[ "$LATEST_DB" == *.enc ]]; then
    if openssl enc -d -aes-256-cbc -pbkdf2 \
        -in "$LATEST_DB" \
        -pass pass:"$BACKUP_ENCRYPTION_KEY" \
        2>/dev/null | head -c 1 > /dev/null; then
        echo "OK: Encryption valid"
    else
        echo "ERROR: Cannot decrypt backup"
        exit 1
    fi
fi

# Test gzip integrity
if [[ "$LATEST_DB" == *.gz ]] || [[ "$LATEST_DB" == *.gz.enc ]]; then
    # Decrypt if needed, then test gzip
    if gzip -t "$LATEST_DB" 2>/dev/null || \
       openssl enc -d -aes-256-cbc -pbkdf2 \
           -in "$LATEST_DB" \
           -pass pass:"$BACKUP_ENCRYPTION_KEY" 2>/dev/null | gzip -t 2>/dev/null; then
        echo "OK: Gzip integrity valid"
    else
        echo "ERROR: Gzip integrity check failed"
        exit 1
    fi
fi

echo "Backup verification passed"
```

### 6.2 Monthly Recovery Test

Schedule monthly recovery tests:

```bash
# Create test environment
docker compose -f docker-compose.workbench.yml -p workbench-test up -d postgres

# Restore to test database
docker exec -i workbench-test-postgres psql -U workbench -d postgres << EOF
CREATE DATABASE workbench_test;
EOF

# Restore backup
zcat /opt/workbench/backups/daily/db_latest.sql.gz | \
    docker exec -i workbench-test-postgres psql -U workbench -d workbench_test

# Run verification queries
docker exec workbench-test-postgres psql -U workbench -d workbench_test << EOF
SELECT count(*) FROM workbench.users;
SELECT count(*) FROM workbench.notebooks;
SELECT count(*) FROM workbench.pipelines;
SELECT count(*) FROM bronze.documents;
EOF

# Cleanup
docker compose -f docker-compose.workbench.yml -p workbench-test down -v
```

---

## 7. Monitoring Backups

### 7.1 Backup Status Check

```bash
# Add to monitoring/alerting
check_backup_age() {
    LATEST=$(ls -t /opt/workbench/backups/daily/db_*.sql.gz* | head -1)
    AGE_HOURS=$(( ($(date +%s) - $(stat -c%Y "$LATEST")) / 3600 ))

    if [ "$AGE_HOURS" -gt 24 ]; then
        echo "CRITICAL: Backup is $AGE_HOURS hours old"
        return 2
    elif [ "$AGE_HOURS" -gt 12 ]; then
        echo "WARNING: Backup is $AGE_HOURS hours old"
        return 1
    else
        echo "OK: Backup is $AGE_HOURS hours old"
        return 0
    fi
}
```

### 7.2 Disk Space Monitoring

```bash
# Alert if backup disk > 80%
BACKUP_DISK_USAGE=$(df /opt/workbench/backups | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$BACKUP_DISK_USAGE" -gt 80 ]; then
    echo "WARNING: Backup disk usage at $BACKUP_DISK_USAGE%"
fi
```

---

## 8. Retention Policy

### 8.1 Automated Cleanup

The backup script handles cleanup automatically. Manual cleanup:

```bash
# Remove backups older than 30 days
find /opt/workbench/backups/daily -type f -mtime +30 -delete

# Keep only last 12 weekly backups
ls -t /opt/workbench/backups/weekly/*.sql.gz* | tail -n +13 | xargs rm -f

# Keep only last 12 monthly backups
ls -t /opt/workbench/backups/monthly/*.sql.gz* | tail -n +13 | xargs rm -f
```

### 8.2 Archive to Cold Storage

For compliance/audit requirements:

```bash
# Move old backups to cold storage
aws s3 mv s3://workbench-backups/2024/ \
    s3://workbench-archive/2024/ \
    --recursive \
    --storage-class GLACIER
```

---

## 9. Contact Information

| Role | Contact | Escalation |
|------|---------|------------|
| Primary On-Call | #data-engineering Slack | PagerDuty |
| Backup Admin | DevOps Team | Email |
| Security (Encryption) | Security Team | Phone |
