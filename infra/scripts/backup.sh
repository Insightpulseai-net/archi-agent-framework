#!/bin/bash
# ============================================================================
# Data Engineering Workbench - Backup Script
# ============================================================================
# Creates encrypted backups of PostgreSQL database and important files.
#
# Usage:
#   ./backup.sh [full|db|files]
#
# Cron example (daily at 2 AM):
#   0 2 * * * /opt/workbench/infra/scripts/backup.sh >> /var/log/workbench-backup.log 2>&1
# ============================================================================

set -euo pipefail

# Configuration
BACKUP_TYPE="${1:-full}"
INSTALL_DIR="${INSTALL_DIR:-/opt/workbench}"
BACKUP_DIR="${BACKUP_DIR:-$INSTALL_DIR/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Load environment variables
if [[ -f "$INSTALL_DIR/infra/.env.workbench" ]]; then
    set -a
    source "$INSTALL_DIR/infra/.env.workbench"
    set +a
fi

# Defaults if not in env
POSTGRES_USER="${POSTGRES_USER:-workbench}"
POSTGRES_DB="${POSTGRES_DB:-workbench}"
BACKUP_ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${RED}[ERROR]${NC} $1"; }

# Create backup directory structure
setup_dirs() {
    mkdir -p "$BACKUP_DIR"/{daily,weekly,monthly}
    mkdir -p "$BACKUP_DIR/tmp"
}

# Backup PostgreSQL database
backup_database() {
    log_info "Backing up PostgreSQL database..."

    local backup_file="$BACKUP_DIR/tmp/db_${TIMESTAMP}.sql"
    local compressed_file="$BACKUP_DIR/daily/db_${TIMESTAMP}.sql.gz"

    # Dump database using docker exec
    docker exec workbench-postgres pg_dump \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        --no-owner \
        --no-acl \
        > "$backup_file"

    # Compress the backup
    gzip -c "$backup_file" > "$compressed_file"

    # Encrypt if key is provided
    if [[ -n "$BACKUP_ENCRYPTION_KEY" ]]; then
        openssl enc -aes-256-cbc -salt -pbkdf2 \
            -in "$compressed_file" \
            -out "${compressed_file}.enc" \
            -pass pass:"$BACKUP_ENCRYPTION_KEY"
        rm "$compressed_file"
        compressed_file="${compressed_file}.enc"
    fi

    # Cleanup temp file
    rm -f "$backup_file"

    # Calculate size
    local size=$(du -h "$compressed_file" | cut -f1)
    log_success "Database backup complete: $compressed_file ($size)"

    echo "$compressed_file"
}

# Backup files (notebooks, uploads, config)
backup_files() {
    log_info "Backing up files..."

    local backup_file="$BACKUP_DIR/daily/files_${TIMESTAMP}.tar.gz"

    # Create tarball of important directories
    tar -czf "$backup_file" \
        -C "$INSTALL_DIR" \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='node_modules' \
        --exclude='.git' \
        data/ \
        infra/.env.workbench \
        2>/dev/null || true

    # Encrypt if key is provided
    if [[ -n "$BACKUP_ENCRYPTION_KEY" ]]; then
        openssl enc -aes-256-cbc -salt -pbkdf2 \
            -in "$backup_file" \
            -out "${backup_file}.enc" \
            -pass pass:"$BACKUP_ENCRYPTION_KEY"
        rm "$backup_file"
        backup_file="${backup_file}.enc"
    fi

    local size=$(du -h "$backup_file" | cut -f1)
    log_success "Files backup complete: $backup_file ($size)"

    echo "$backup_file"
}

# Backup Docker volumes
backup_volumes() {
    log_info "Backing up Docker volumes..."

    local backup_file="$BACKUP_DIR/daily/volumes_${TIMESTAMP}.tar.gz"

    # Get volume data
    docker run --rm \
        -v workbench-notebooks:/notebooks:ro \
        -v workbench-uploads:/uploads:ro \
        -v "$BACKUP_DIR/tmp":/backup \
        alpine tar -czf /backup/volumes.tar.gz /notebooks /uploads

    mv "$BACKUP_DIR/tmp/volumes.tar.gz" "$backup_file"

    # Encrypt if key is provided
    if [[ -n "$BACKUP_ENCRYPTION_KEY" ]]; then
        openssl enc -aes-256-cbc -salt -pbkdf2 \
            -in "$backup_file" \
            -out "${backup_file}.enc" \
            -pass pass:"$BACKUP_ENCRYPTION_KEY"
        rm "$backup_file"
        backup_file="${backup_file}.enc"
    fi

    local size=$(du -h "$backup_file" | cut -f1)
    log_success "Volumes backup complete: $backup_file ($size)"

    echo "$backup_file"
}

# Rotate old backups
rotate_backups() {
    log_info "Rotating old backups (keeping ${RETENTION_DAYS} days)..."

    # Daily backups: keep for RETENTION_DAYS
    find "$BACKUP_DIR/daily" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null || true

    # Weekly backups: keep for 90 days
    find "$BACKUP_DIR/weekly" -type f -mtime +90 -delete 2>/dev/null || true

    # Monthly backups: keep for 365 days
    find "$BACKUP_DIR/monthly" -type f -mtime +365 -delete 2>/dev/null || true

    log_success "Backup rotation complete"
}

# Copy to weekly/monthly if applicable
promote_backup() {
    local latest_db=$(ls -t "$BACKUP_DIR/daily"/db_*.sql.gz* 2>/dev/null | head -1)
    local latest_files=$(ls -t "$BACKUP_DIR/daily"/files_*.tar.gz* 2>/dev/null | head -1)

    # Weekly backup on Sundays
    if [[ $(date +%u) -eq 7 ]]; then
        log_info "Creating weekly backup copy..."
        [[ -f "$latest_db" ]] && cp "$latest_db" "$BACKUP_DIR/weekly/"
        [[ -f "$latest_files" ]] && cp "$latest_files" "$BACKUP_DIR/weekly/"
    fi

    # Monthly backup on 1st of month
    if [[ $(date +%d) -eq 01 ]]; then
        log_info "Creating monthly backup copy..."
        [[ -f "$latest_db" ]] && cp "$latest_db" "$BACKUP_DIR/monthly/"
        [[ -f "$latest_files" ]] && cp "$latest_files" "$BACKUP_DIR/monthly/"
    fi
}

# Verify backup integrity
verify_backup() {
    local backup_file="$1"
    log_info "Verifying backup: $backup_file"

    if [[ "$backup_file" == *.enc ]]; then
        # Encrypted backup - test decryption
        if openssl enc -d -aes-256-cbc -pbkdf2 \
            -in "$backup_file" \
            -pass pass:"$BACKUP_ENCRYPTION_KEY" \
            2>/dev/null | head -c 1 > /dev/null; then
            log_success "Backup verified: $backup_file"
            return 0
        else
            log_error "Backup verification failed: $backup_file"
            return 1
        fi
    elif [[ "$backup_file" == *.gz ]]; then
        # Gzip - test integrity
        if gzip -t "$backup_file" 2>/dev/null; then
            log_success "Backup verified: $backup_file"
            return 0
        else
            log_error "Backup verification failed: $backup_file"
            return 1
        fi
    fi
}

# Upload to remote storage (optional)
upload_to_remote() {
    local backup_file="$1"

    # Skip if no S3 config
    if [[ -z "${BACKUP_S3_BUCKET:-}" ]]; then
        return 0
    fi

    log_info "Uploading to remote storage: $backup_file"

    # Using AWS CLI or s3cmd
    if command -v aws &> /dev/null; then
        aws s3 cp "$backup_file" "s3://$BACKUP_S3_BUCKET/workbench/$(basename "$backup_file")"
        log_success "Uploaded to S3: $backup_file"
    elif command -v s3cmd &> /dev/null; then
        s3cmd put "$backup_file" "s3://$BACKUP_S3_BUCKET/workbench/$(basename "$backup_file")"
        log_success "Uploaded to S3: $backup_file"
    else
        log_warn "No S3 CLI available, skipping remote upload"
    fi
}

# Send notification
send_notification() {
    local status="$1"
    local message="$2"

    # Slack notification (if configured)
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local color="good"
        [[ "$status" == "error" ]] && color="danger"

        curl -s -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-Type: application/json' \
            -d "{
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"title\": \"Workbench Backup $status\",
                    \"text\": \"$message\",
                    \"ts\": $(date +%s)
                }]
            }" > /dev/null
    fi
}

# Main backup function
main() {
    log_info "Starting backup (type: $BACKUP_TYPE)..."
    echo ""

    setup_dirs

    local db_backup=""
    local files_backup=""
    local volumes_backup=""
    local errors=0

    case "$BACKUP_TYPE" in
        full)
            db_backup=$(backup_database) || ((errors++))
            files_backup=$(backup_files) || ((errors++))
            volumes_backup=$(backup_volumes) || ((errors++))
            ;;
        db)
            db_backup=$(backup_database) || ((errors++))
            ;;
        files)
            files_backup=$(backup_files) || ((errors++))
            volumes_backup=$(backup_volumes) || ((errors++))
            ;;
        *)
            log_error "Unknown backup type: $BACKUP_TYPE"
            exit 1
            ;;
    esac

    # Verify backups
    [[ -n "$db_backup" ]] && verify_backup "$db_backup" || ((errors++))
    [[ -n "$files_backup" ]] && verify_backup "$files_backup" || ((errors++))

    # Upload to remote
    [[ -n "$db_backup" ]] && upload_to_remote "$db_backup"
    [[ -n "$files_backup" ]] && upload_to_remote "$files_backup"

    # Rotate old backups
    rotate_backups

    # Promote to weekly/monthly
    promote_backup

    # Cleanup tmp
    rm -rf "$BACKUP_DIR/tmp"/*

    # Summary
    echo ""
    if [[ $errors -eq 0 ]]; then
        log_success "Backup completed successfully!"
        send_notification "success" "Backup completed successfully at $(date)"
    else
        log_error "Backup completed with $errors errors"
        send_notification "error" "Backup completed with $errors errors at $(date)"
        exit 1
    fi
}

main "$@"
