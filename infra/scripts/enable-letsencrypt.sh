#!/bin/bash
# ============================================================================
# Let's Encrypt Certificate Setup for Data Engineering Workbench
# ============================================================================
# This script obtains and configures SSL certificates using Certbot.
#
# Usage:
#   sudo bash enable-letsencrypt.sh [domain] [email]
#
# Example:
#   sudo bash enable-letsencrypt.sh workbench.insightpulseai.net admin@insightpulseai.net
# ============================================================================

set -euo pipefail

# Configuration
DOMAIN="${1:-workbench.insightpulseai.net}"
EMAIL="${2:-admin@insightpulseai.net}"
CERT_DIR="/opt/workbench/infra/nginx/ssl"
WEBROOT="/opt/workbench/infra/nginx/certbot"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root"
    exit 1
fi

# Install certbot if not present
if ! command -v certbot &> /dev/null; then
    log_info "Installing Certbot..."
    apt-get update -qq
    apt-get install -y -qq certbot python3-certbot-nginx
fi

# Create webroot directory
mkdir -p "$WEBROOT"
mkdir -p "$CERT_DIR"

# Create temporary nginx config for certificate validation
create_temp_nginx_config() {
    log_info "Creating temporary nginx configuration..."

    cat > /etc/nginx/sites-available/certbot-temp << EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    location /.well-known/acme-challenge/ {
        root $WEBROOT;
    }

    location / {
        return 301 https://\$host\$request_uri;
    }
}
EOF

    ln -sf /etc/nginx/sites-available/certbot-temp /etc/nginx/sites-enabled/certbot-temp
    nginx -t && systemctl reload nginx
}

# Obtain certificate
obtain_certificate() {
    log_info "Obtaining certificate for $DOMAIN..."

    certbot certonly \
        --webroot \
        --webroot-path "$WEBROOT" \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --non-interactive \
        -d "$DOMAIN"

    log_success "Certificate obtained successfully"
}

# Copy certificates to workbench directory
copy_certificates() {
    log_info "Copying certificates to workbench directory..."

    cp /etc/letsencrypt/live/"$DOMAIN"/fullchain.pem "$CERT_DIR/"
    cp /etc/letsencrypt/live/"$DOMAIN"/privkey.pem "$CERT_DIR/"
    cp /etc/letsencrypt/live/"$DOMAIN"/chain.pem "$CERT_DIR/"

    # Set permissions
    chmod 644 "$CERT_DIR"/fullchain.pem
    chmod 644 "$CERT_DIR"/chain.pem
    chmod 600 "$CERT_DIR"/privkey.pem

    log_success "Certificates copied to $CERT_DIR"
}

# Setup auto-renewal
setup_renewal() {
    log_info "Setting up auto-renewal..."

    # Create renewal hook script
    cat > /etc/letsencrypt/renewal-hooks/deploy/workbench-reload.sh << EOF
#!/bin/bash
# Copy renewed certificates to workbench
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $CERT_DIR/
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem $CERT_DIR/
cp /etc/letsencrypt/live/$DOMAIN/chain.pem $CERT_DIR/

# Set permissions
chmod 644 $CERT_DIR/fullchain.pem
chmod 644 $CERT_DIR/chain.pem
chmod 600 $CERT_DIR/privkey.pem

# Reload nginx
docker exec workbench-nginx nginx -s reload 2>/dev/null || systemctl reload nginx
EOF

    chmod +x /etc/letsencrypt/renewal-hooks/deploy/workbench-reload.sh

    # Test renewal
    certbot renew --dry-run

    log_success "Auto-renewal configured"
}

# Remove temporary config
cleanup_temp_config() {
    log_info "Cleaning up temporary configuration..."
    rm -f /etc/nginx/sites-enabled/certbot-temp
    rm -f /etc/nginx/sites-available/certbot-temp
    nginx -t && systemctl reload nginx
}

# Main execution
main() {
    echo ""
    log_info "Setting up Let's Encrypt for $DOMAIN"
    echo ""

    create_temp_nginx_config
    obtain_certificate
    copy_certificates
    setup_renewal
    cleanup_temp_config

    echo ""
    log_success "SSL setup complete!"
    echo ""
    echo "Certificates are located at:"
    echo "  - Certificate: $CERT_DIR/fullchain.pem"
    echo "  - Private Key: $CERT_DIR/privkey.pem"
    echo "  - Chain: $CERT_DIR/chain.pem"
    echo ""
    echo "Auto-renewal is configured and will run automatically."
    echo ""
}

main "$@"
