#!/bin/bash
# Bridge Kit - Validation & Testing
# Verifies all credentials and APIs are accessible

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"

echo "✔️  Bridge Kit Validation"
echo "========================"
echo ""

# Load .env
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env not found"
    exit 1
fi

set -a
source "$ENV_FILE"
set +a

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}✅ $1${NC}"; }
fail() { echo -e "${RED}❌ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# Test 1: Check required files
echo "Test 1: Checking required files..."
[ -f "$GITHUB_APP_PRIVATE_KEY_PATH" ] && pass "Private key found" || fail "Private key not found at $GITHUB_APP_PRIVATE_KEY_PATH"

# Test 2: Validate .env variables
echo ""
echo "Test 2: Validating .env variables..."
for var in GITHUB_APP_ID GITHUB_APP_INSTALLATION_ID N8N_BASE_URL GITHUB_ORG PRIMARY_REPO; do
    val=$(eval echo \$$var)
    if [ -z "$val" ] || [[ "$val" == *"YOUR_"* ]]; then
        fail "$var not configured"
    else
        pass "$var = $val"
    fi
done

# Test 3: Test GitHub API connectivity
echo ""
echo "Test 3: Testing GitHub API (no auth required)..."
if curl -s -I https://api.github.com | grep -q "200\|301\|302"; then
    pass "GitHub API is accessible"
else
    fail "Cannot reach GitHub API"
fi

# Test 4: Test n8n connectivity
echo ""
echo "Test 4: Testing n8n connectivity..."
if curl -s -I "$N8N_BASE_URL" | grep -q "200\|301\|302\|401\|403"; then
    pass "n8n server is accessible"
else
    fail "Cannot reach n8n at $N8N_BASE_URL"
fi

# Test 5: Generate JWT for GitHub App (if openssl available)
echo ""
echo "Test 5: Testing JWT generation for GitHub App..."
if command -v openssl &> /dev/null; then
    # Create JWT header and payload
    HEADER=$(echo -n '{"alg":"RS256","typ":"JWT"}' | base64 | tr '+/' '-_' | tr -d '=')
    NOW=$(date +%s)
    EXP=$((NOW + 600))
    PAYLOAD=$(echo -n "{\"iss\":\"$GITHUB_APP_ID\",\"iat\":$NOW,\"exp\":$EXP}" | base64 | tr '+/' '-_' | tr -d '=')

    # Sign with private key
    MESSAGE="$HEADER.$PAYLOAD"
    SIGNATURE=$(echo -n "$MESSAGE" | openssl dgst -sha256 -sign "$GITHUB_APP_PRIVATE_KEY_PATH" | base64 | tr '+/' '-_' | tr -d '=')
    JWT="$MESSAGE.$SIGNATURE"

    if [ ${#JWT} -gt 100 ]; then
        pass "JWT generated successfully (${#JWT} chars)"
    else
        fail "JWT generation failed"
    fi
else
    warn "openssl not found, skipping JWT test"
fi

# Test 6: Test GitHub API with JWT
echo ""
echo "Test 6: Testing GitHub API authentication..."
if [ -n "$JWT" ]; then
    RESPONSE=$(curl -s -H "Authorization: Bearer $JWT" \
        -H "Accept: application/vnd.github+json" \
        https://api.github.com/app)

    if echo "$RESPONSE" | grep -q "$GITHUB_APP_ID"; then
        pass "GitHub App authentication successful"
    elif echo "$RESPONSE" | grep -q '"name"'; then
        pass "GitHub API responding to authenticated requests"
    else
        fail "GitHub authentication failed: $(echo "$RESPONSE" | head -c 100)"
    fi
else
    warn "Skipping GitHub API auth test (no JWT)"
fi

# Test 7: Verify n8n MCP endpoint
echo ""
echo "Test 7: Testing n8n MCP server..."
MCP_URL="${N8N_MCP_SERVER_URL:-$N8N_BASE_URL/mcp-server/http}"
if curl -s -I "$MCP_URL" | grep -q "200\|401\|403"; then
    pass "n8n MCP server is accessible"
else
    warn "Could not verify n8n MCP server (may require auth)"
fi

echo ""
echo "✅ Validation complete!"
echo ""
echo "🚀 Next steps:"
echo "   1. Review any failures above"
echo "   2. Run: ./scripts/deploy.sh --target n8n"
echo "   3. Run: ./scripts/test.sh --integration n8n"
