#!/bin/bash
# ============================================================================
# Data Engineering Workbench - Droplet Setup Script
# ============================================================================
# This script sets up a fresh DigitalOcean droplet for the workbench.
# Run as root or with sudo.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/your-org/fin-workspace-automation/main/infra/scripts/setup-workbench-droplet.sh | bash
#
# Or clone repo first:
#   git clone https://github.com/your-org/fin-workspace-automation.git
#   cd fin-workspace-automation
#   sudo bash infra/scripts/setup-workbench-droplet.sh
# ============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="${REPO_URL:-https://github.com/your-org/fin-workspace-automation.git}"
INSTALL_DIR="${INSTALL_DIR:-/opt/workbench}"
WORKBENCH_USER="${WORKBENCH_USER:-workbench}"
DOMAIN="${DOMAIN:-workbench.insightpulseai.net}"

# Logging
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

# Update system packages
update_system() {
    log_info "Updating system packages..."
    apt-get update -qq
    apt-get upgrade -y -qq
    log_success "System packages updated"
}

# Install required packages
install_dependencies() {
    log_info "Installing dependencies..."
    apt-get install -y -qq \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release \
        git \
        jq \
        htop \
        vim \
        ufw \
        fail2ban \
        unzip \
        software-properties-common
    log_success "Dependencies installed"
}

# Install Docker
install_docker() {
    if command -v docker &> /dev/null; then
        log_info "Docker already installed: $(docker --version)"
        return 0
    fi

    log_info "Installing Docker..."

    # Add Docker's official GPG key
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    # Add Docker repository
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
        tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Enable and start Docker
    systemctl enable docker
    systemctl start docker

    log_success "Docker installed: $(docker --version)"
}

# Create workbench user
create_user() {
    if id "$WORKBENCH_USER" &>/dev/null; then
        log_info "User $WORKBENCH_USER already exists"
        return 0
    fi

    log_info "Creating user: $WORKBENCH_USER..."
    useradd -m -s /bin/bash "$WORKBENCH_USER"
    usermod -aG docker "$WORKBENCH_USER"
    log_success "User $WORKBENCH_USER created and added to docker group"
}

# Configure firewall
configure_firewall() {
    log_info "Configuring firewall..."

    # Allow SSH
    ufw allow 22/tcp comment 'SSH'

    # Allow HTTP/HTTPS
    ufw allow 80/tcp comment 'HTTP'
    ufw allow 443/tcp comment 'HTTPS'

    # Enable firewall (non-interactive)
    ufw --force enable

    log_success "Firewall configured"
    ufw status verbose
}

# Configure fail2ban
configure_fail2ban() {
    log_info "Configuring fail2ban..."

    cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5
backend = systemd

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 24h
EOF

    systemctl enable fail2ban
    systemctl restart fail2ban
    log_success "fail2ban configured"
}

# Clone or update repository
setup_repository() {
    log_info "Setting up repository..."

    if [[ -d "$INSTALL_DIR" ]]; then
        log_info "Repository exists, pulling latest changes..."
        cd "$INSTALL_DIR"
        git pull origin main || log_warn "Could not pull latest changes"
    else
        log_info "Cloning repository..."
        git clone "$REPO_URL" "$INSTALL_DIR"
    fi

    # Set ownership
    chown -R "$WORKBENCH_USER:$WORKBENCH_USER" "$INSTALL_DIR"
    log_success "Repository set up at $INSTALL_DIR"
}

# Create required directories
create_directories() {
    log_info "Creating required directories..."

    mkdir -p "$INSTALL_DIR"/{data,logs,backups}
    mkdir -p "$INSTALL_DIR"/infra/nginx/ssl
    mkdir -p "$INSTALL_DIR"/infra/nginx/certbot
    mkdir -p /var/log/nginx

    chown -R "$WORKBENCH_USER:$WORKBENCH_USER" "$INSTALL_DIR"

    log_success "Directories created"
}

# Setup environment file
setup_env() {
    log_info "Setting up environment file..."

    ENV_FILE="$INSTALL_DIR/infra/.env.workbench"

    if [[ -f "$ENV_FILE" ]]; then
        log_warn "Environment file already exists, skipping..."
        return 0
    fi

    # Copy example and generate secrets
    cp "$INSTALL_DIR/infra/.env.workbench.example" "$ENV_FILE"

    # Generate random secrets
    SECRET_KEY=$(openssl rand -hex 32)
    ENCRYPTION_KEY=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 32)
    POSTGRES_PASSWORD=$(openssl rand -hex 24)
    JUPYTER_TOKEN=$(openssl rand -hex 32)
    MINIO_ACCESS_KEY=$(openssl rand -hex 16)
    MINIO_SECRET_KEY=$(openssl rand -hex 32)
    NEXTAUTH_SECRET=$(openssl rand -hex 32)
    BACKUP_ENCRYPTION_KEY=$(openssl rand -hex 32)

    # Update secrets in env file
    sed -i "s/your-secret-key-here-generate-with-openssl/$SECRET_KEY/" "$ENV_FILE"
    sed -i "s/your-encryption-key-here-generate-with-openssl/$ENCRYPTION_KEY/" "$ENV_FILE"
    sed -i "s/your-jwt-secret-here-generate-with-openssl/$JWT_SECRET/" "$ENV_FILE"
    sed -i "s/your-strong-postgres-password-here/$POSTGRES_PASSWORD/g" "$ENV_FILE"
    sed -i "s/your-jupyter-token-here/$JUPYTER_TOKEN/" "$ENV_FILE"
    sed -i "s/your-minio-access-key/$MINIO_ACCESS_KEY/" "$ENV_FILE"
    sed -i "s/your-minio-secret-key/$MINIO_SECRET_KEY/" "$ENV_FILE"
    sed -i "s/your-nextauth-secret-here/$NEXTAUTH_SECRET/" "$ENV_FILE"
    sed -i "s/your-backup-encryption-key/$BACKUP_ENCRYPTION_KEY/" "$ENV_FILE"

    # Secure the file
    chmod 600 "$ENV_FILE"
    chown "$WORKBENCH_USER:$WORKBENCH_USER" "$ENV_FILE"

    log_success "Environment file created with generated secrets"
    log_warn "Please update $ENV_FILE with your actual API keys and service credentials"
}

# Install nginx (for standalone use)
install_nginx() {
    if command -v nginx &> /dev/null; then
        log_info "nginx already installed"
        return 0
    fi

    log_info "Installing nginx..."
    apt-get install -y -qq nginx

    systemctl enable nginx
    systemctl start nginx

    log_success "nginx installed"
}

# Setup Let's Encrypt with Certbot
setup_certbot() {
    log_info "Setting up Certbot..."

    if ! command -v certbot &> /dev/null; then
        apt-get install -y -qq certbot python3-certbot-nginx
    fi

    log_success "Certbot installed"
    log_info "Run 'certbot --nginx -d $DOMAIN' to obtain certificates"
}

# Create systemd service for docker compose
create_systemd_service() {
    log_info "Creating systemd service..."

    cat > /etc/systemd/system/workbench.service << EOF
[Unit]
Description=Data Engineering Workbench
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$INSTALL_DIR/infra
ExecStart=/usr/bin/docker compose -f docker-compose.workbench.yml --env-file .env.workbench up -d
ExecStop=/usr/bin/docker compose -f docker-compose.workbench.yml --env-file .env.workbench down
User=$WORKBENCH_USER

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable workbench

    log_success "Systemd service created (workbench.service)"
}

# Setup backup cron job
setup_backup_cron() {
    log_info "Setting up backup cron job..."

    BACKUP_SCRIPT="$INSTALL_DIR/infra/scripts/backup.sh"

    if [[ ! -f "$BACKUP_SCRIPT" ]]; then
        log_warn "Backup script not found, skipping cron setup"
        return 0
    fi

    # Make backup script executable
    chmod +x "$BACKUP_SCRIPT"

    # Add cron job for daily backups at 2 AM
    (crontab -l 2>/dev/null | grep -v "$BACKUP_SCRIPT"; echo "0 2 * * * $BACKUP_SCRIPT >> /var/log/workbench-backup.log 2>&1") | crontab -

    log_success "Backup cron job configured"
}

# Print next steps
print_next_steps() {
    echo ""
    echo "=============================================="
    echo "  Setup Complete!"
    echo "=============================================="
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Update environment variables:"
    echo "   nano $INSTALL_DIR/infra/.env.workbench"
    echo ""
    echo "2. Configure SSL certificates:"
    echo "   certbot --nginx -d $DOMAIN"
    echo ""
    echo "3. Start the workbench:"
    echo "   systemctl start workbench"
    echo ""
    echo "4. Or manually with docker compose:"
    echo "   cd $INSTALL_DIR/infra"
    echo "   docker compose -f docker-compose.workbench.yml --env-file .env.workbench up -d"
    echo ""
    echo "5. Check status:"
    echo "   docker compose -f docker-compose.workbench.yml ps"
    echo ""
    echo "6. View logs:"
    echo "   docker compose -f docker-compose.workbench.yml logs -f"
    echo ""
    echo "=============================================="
}

# Main function
main() {
    log_info "Starting Data Engineering Workbench setup..."
    echo ""

    check_root
    update_system
    install_dependencies
    install_docker
    create_user
    configure_firewall
    configure_fail2ban
    install_nginx
    setup_certbot
    create_directories
    setup_repository
    setup_env
    create_systemd_service
    setup_backup_cron

    print_next_steps
}

# Run main function
main "$@"
