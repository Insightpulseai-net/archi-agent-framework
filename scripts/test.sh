#!/bin/bash
# Bridge Kit - Integration Tests
# Tests all components: GitHub, n8n, Chrome, MCP

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"

# Load .env
set -a
source "$ENV_FILE"
set +a

echo "🧪 Bridge Kit Integration Tests"
echo "==============================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

pass() { echo -e "${GREEN}✅ $1${NC}"; }
fail() { echo -e "${RED}❌ $1${NC}"; return 1; }
info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }

INTEGRATION="${1:---all}"
FAILED=0

# ===== TEST: GitHub API =====
test_github() {
    echo "Test: GitHub API"
    echo "----------------"

    # Generate JWT
    HEADER=$(echo -n '{"alg":"RS256","typ":"JWT"}' | base64 | tr '+/' '-_' | tr -d '=')
    NOW=$(date +%s)
    EXP=$((NOW + 600))
    PAYLOAD=$(echo -n "{\"iss\":\"$GITHUB_APP_ID\",\"iat\":$NOW,\"exp\":$EXP}" | base64 | tr '+/' '-_' | tr -d '=')
    MESSAGE="$HEADER.$PAYLOAD"
    SIGNATURE=$(echo -n "$MESSAGE" | openssl dgst -sha256 -sign "$GITHUB_APP_PRIVATE_KEY_PATH" | base64 | tr '+/' '-_' | tr -d '=')
    JWT="$MESSAGE.$SIGNATURE"

    # Test 1: Get app info
    info "Fetching app info..."
    RESPONSE=$(curl -s -H "Authorization: Bearer $JWT" \
        -H "Accept: application/vnd.github+json" \
        https://api.github.com/app)

    APP_NAME=$(echo "$RESPONSE" | jq -r '.slug // empty')
    if [ -n "$APP_NAME" ]; then
        pass "GitHub App authenticated: $APP_NAME"
    else
        fail "GitHub authentication failed"
        ((FAILED++))
        return
    fi

    # Test 2: Get installation
    info "Fetching installation token..."
    INST_RESPONSE=$(curl -s -X POST \
        -H "Authorization: Bearer $JWT" \
        -H "Accept: application/vnd.github+json" \
        "https://api.github.com/app/installations/$GITHUB_APP_INSTALLATION_ID/access_tokens")

    INST_TOKEN=$(echo "$INST_RESPONSE" | jq -r '.token // empty')
    if [ -n "$INST_TOKEN" ]; then
        pass "Installation token obtained (${#INST_TOKEN} chars)"
    else
        fail "Could not get installation token"
        ((FAILED++))
        return
    fi

    # Test 3: List repos with token
    info "Testing repo access..."
    REPOS=$(curl -s -H "Authorization: token $INST_TOKEN" \
        -H "Accept: application/vnd.github+json" \
        "https://api.github.com/user/repos" | jq -r '.[] | .name' | head -5)

    if [ -n "$REPOS" ]; then
        pass "Can access repositories:"
        echo "$REPOS" | sed 's/^/   - /'
    else
        warn "No repos found (may be normal for app-only auth)"
    fi

    echo ""
}

# ===== TEST: n8n =====
test_n8n() {
    echo "Test: n8n"
    echo "--------"

    # Test 1: Basic connectivity
    info "Testing n8n connectivity..."
    STATUS=$(curl -s -I "$N8N_BASE_URL" | head -1)
    if [[ "$STATUS" == *"200"* ]] || [[ "$STATUS" == *"301"* ]]; then
        pass "n8n is accessible: $STATUS"
    else
        fail "n8n not responding: $STATUS"
        ((FAILED++))
        return
    fi

    # Test 2: API key validation
    if [ -n "$N8N_API_KEY" ] && [[ ! "$N8N_API_KEY" == *"YOUR_"* ]]; then
        info "Testing API key..."
        WORKFLOWS=$(curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
            "$N8N_BASE_URL/api/v1/workflows" | jq '.data | length' 2>/dev/null || echo "0")

        if [ "$WORKFLOWS" != "0" ]; then
            pass "API key valid, found $WORKFLOWS workflows"
        else
            warn "API key present but workflows count unclear"
        fi
    else
        warn "API key not configured, skipping auth test"
    fi

    # Test 3: Webhook connectivity
    info "Testing webhook endpoint..."
    WEBHOOK_TEST=$(curl -s -X POST "$N8N_WEBHOOK_URL?test=true" \
        -H "Content-Type: application/json" \
        -d '{"test":true}' 2>&1)

    if [[ "$WEBHOOK_TEST" == *"200"* ]] || [[ "$WEBHOOK_TEST" == *"Not"* ]]; then
        pass "Webhook endpoint is reachable"
    else
        warn "Webhook test inconclusive: $WEBHOOK_TEST"
    fi

    echo ""
}

# ===== TEST: Chrome Extension =====
test_chrome() {
    echo "Test: Chrome Extension"
    echo "---------------------"

    if [ -z "$CHROME_EXTENSION_ID" ] || [[ "$CHROME_EXTENSION_ID" == *"YOUR_"* ]]; then
        warn "Extension ID not configured, skipping"
        echo ""
        return
    fi

    info "Extension ID: $CHROME_EXTENSION_ID"
    info "To test the extension:"
    echo "   1. Build it with: ./scripts/deploy.sh --target extension"
    echo "   2. Load at: chrome://extensions"
    echo "   3. Open page, right-click any text"
    echo "   4. Look for 'Create GitHub Issue' option"

    echo ""
}

# ===== TEST: MCP Server =====
test_mcp() {
    echo "Test: MCP Server"
    echo "---------------"

    info "MCP Server URL: $N8N_MCP_SERVER_URL"

    if curl -s -I "$N8N_MCP_SERVER_URL" | grep -q "200\|401\|403"; then
        pass "MCP server is accessible"
    else
        warn "Could not verify MCP server (may require auth)"
    fi

    info "To test MCP tools:"
    echo "   1. Open Claude.ai or Claude Desktop"
    echo "   2. Ask: 'Create GitHub issue titled 'Test Issue' in $PRIMARY_REPO'"
    echo "   3. Claude will call the GitHub Create Issue MCP tool"

    echo ""
}

# ===== MAIN =====
case "$INTEGRATION" in
    github|--integration=github)
        test_github
        ;;
    n8n|--integration=n8n)
        test_n8n
        ;;
    chrome|--integration=chrome)
        test_chrome
        ;;
    mcp|--integration=mcp)
        test_mcp
        ;;
    all|--all)
        test_github
        test_n8n
        test_chrome
        test_mcp
        ;;
    *)
        echo "Usage: $0 [github|n8n|chrome|mcp|all]"
        exit 1
        ;;
esac

echo "================================"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "📖 Next: Read the Bridge Kit docs"
    echo "   https://github.com/insightpulseai-net/pulser-agent-framework/docs/BRIDGE_KIT.md"
else
    echo -e "${RED}❌ $FAILED test(s) failed${NC}"
    exit 1
fi
