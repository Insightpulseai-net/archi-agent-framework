#!/bin/bash
# Bridge Kit - Interactive Credential Setup
# Prompts for all required credentials securely

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"

echo "🔐 Bridge Kit Credential Setup"
echo "=============================="
echo ""

# Ensure .env exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env not found. Run: ./scripts/generate-env.sh"
    exit 1
fi

# Helper function to update .env
update_env() {
    local key="$1"
    local value="$2"

    if grep -q "^$key=" "$ENV_FILE"; then
        # Use | as delimiter to handle paths with /
        sed -i.bak "s|^$key=.*|$key=$value|" "$ENV_FILE"
    else
        echo "$key=$value" >> "$ENV_FILE"
    fi
}

# Helper to read secure input (no echo)
read_secret() {
    local prompt="$1"
    local var_name="$2"

    echo -n "$prompt: "
    read -rs value
    echo ""

    if [ -n "$value" ]; then
        update_env "$var_name" "$value"
        echo "✅ Set $var_name"
    fi
}

# Helper to read normal input
read_input() {
    local prompt="$1"
    local var_name="$2"
    local default="$3"

    if [ -n "$default" ]; then
        echo -n "$prompt [$default]: "
    else
        echo -n "$prompt: "
    fi
    read -r value

    if [ -n "$value" ]; then
        update_env "$var_name" "$value"
        echo "✅ Set $var_name"
    elif [ -n "$default" ]; then
        update_env "$var_name" "$default"
        echo "✅ Set $var_name to default: $default"
    fi
}

# ===== GITHUB APP =====
echo "📌 GITHUB APP CREDENTIALS"
echo "------------------------"
echo "Get these from: https://github.com/settings/apps/pulser-hub"
echo ""

read_input "GitHub App ID" "GITHUB_APP_ID"
read_input "Installation ID" "GITHUB_APP_INSTALLATION_ID"
echo "⚠️  Private key path (download .pem from GitHub App settings)"
read_input "Path to private key" "GITHUB_APP_PRIVATE_KEY_PATH"
read_input "Client ID" "GITHUB_APP_CLIENT_ID"
read_secret "Client Secret (hidden)" "GITHUB_APP_CLIENT_SECRET"

# ===== n8n =====
echo ""
echo "📌 n8n CONFIGURATION"
echo "-------------------"
echo "Base URL should be: https://n8n.insightpulseai.net"
echo ""

read_input "n8n Base URL" "N8N_BASE_URL" "https://n8n.insightpulseai.net"
read_input "n8n Webhook URL" "N8N_WEBHOOK_URL" "https://n8n.insightpulseai.net/webhook/bridge-kit"
read_secret "n8n API Key (hidden)" "N8N_API_KEY"

# ===== CHROME EXTENSION =====
echo ""
echo "📌 CHROME EXTENSION"
echo "------------------"
echo "Get extension ID from: chrome://extensions (after loading unpacked)"
echo ""

read_input "Extension ID (skip if not built yet)" "CHROME_EXTENSION_ID"
read_input "Chrome popup webhook URL" "CHROME_POPUP_WEBHOOK" "https://n8n.insightpulseai.net/webhook/chrome-context"

# ===== REPOS =====
echo ""
echo "📌 GITHUB REPOSITORIES"
echo "---------------------"
read_input "GitHub Organization" "GITHUB_ORG" "insightpulseai"
read_input "Primary Repository" "PRIMARY_REPO" "pulser-agent-framework"
read_input "Issues Repository" "ISSUES_REPO" "insightpulse-tracker"

# ===== SUPABASE =====
echo ""
echo "📌 SUPABASE CONFIGURATION"
echo "------------------------"
echo "Project: spdtwktxdalcfigzeqrz (external managed service)"
echo "Get credentials from: https://supabase.com/dashboard/project/spdtwktxdalcfigzeqrz/settings/api"
echo ""

read_secret "Supabase Anon Key (hidden)" "NEXT_PUBLIC_SUPABASE_ANON_KEY"
read_secret "Supabase Service Role Key (hidden)" "SUPABASE_SERVICE_ROLE_KEY"
read_secret "PostgreSQL Password (hidden)" "POSTGRES_PASSWORD"

# ===== GOOGLE CLOUD =====
echo ""
echo "📌 GOOGLE CLOUD CREDENTIALS"
echo "-------------------------"
echo "Service Account: ipai-docs2code-runner@PROJECT_ID.iam.gserviceaccount.com"
echo "Setup guide: docs/GOOGLE_CREDENTIALS_SETUP.md"
echo ""

read_input "Path to service account JSON" "GOOGLE_SERVICE_ACCOUNT_FILE" "secrets/ipai-docs2code-runner.json"

# ===== ENVIRONMENT =====
echo ""
echo "📌 ENVIRONMENT SETTINGS"
echo "---------------------"
read_input "Environment (development/staging/production)" "ENVIRONMENT" "development"
read_input "Debug mode (true/false)" "DEBUG" "false"
read_input "Log level (debug/info/warn/error)" "LOG_LEVEL" "info"

echo ""
echo "✅ All credentials set!"
echo ""
echo "🔍 Verify with: ./scripts/validate.sh"
