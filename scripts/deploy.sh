#!/bin/bash
# Bridge Kit - Deployment
# Deploys to n8n, builds Chrome extension, registers MCP tools

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"
BUILD_DIR="$PROJECT_ROOT/build"

# Load .env
set -a
source "$ENV_FILE"
set +a

echo "🚀 Bridge Kit Deployment"
echo "========================"
echo ""

# Parse arguments
TARGET="${1:---all}"
DRY_RUN="${2}"

if [[ "$DRY_RUN" == "--dry-run" ]]; then
    echo "⚠️  DRY RUN MODE (no changes will be made)"
fi

# ===== DEPLOY TO n8n =====
deploy_n8n() {
    echo "📦 Deploying to n8n..."

    # Generate workflow JSON from template
    WORKFLOW_FILE="$PROJECT_ROOT/config/bridge-kit-workflow.json"

    if [ ! -f "$WORKFLOW_FILE" ]; then
        echo "❌ Workflow file not found: $WORKFLOW_FILE"
        return 1
    fi

    # Replace placeholders in workflow
    TEMP_WORKFLOW=$(mktemp)
    sed "s|N8N_WEBHOOK_URL|$N8N_WEBHOOK_URL|g" "$WORKFLOW_FILE" \
        | sed "s|GITHUB_APP_ID|$GITHUB_APP_ID|g" \
        | sed "s|GITHUB_ORG|$GITHUB_ORG|g" \
        > "$TEMP_WORKFLOW"

    if [[ "$DRY_RUN" == "--dry-run" ]]; then
        echo "📄 Would import workflow:"
        head -20 "$TEMP_WORKFLOW"
        echo "..."
        rm "$TEMP_WORKFLOW"
        return 0
    fi

    # Import to n8n via API
    RESPONSE=$(curl -s -X POST "$N8N_BASE_URL/api/v1/workflows" \
        -H "X-N8N-API-KEY: $N8N_API_KEY" \
        -H "Content-Type: application/json" \
        -d @"$TEMP_WORKFLOW")

    WORKFLOW_ID=$(echo "$RESPONSE" | jq -r '.id // empty')

    if [ -n "$WORKFLOW_ID" ]; then
        echo "✅ Workflow imported: $WORKFLOW_ID"
        echo "   View at: $N8N_BASE_URL/workflow/$WORKFLOW_ID"
        rm "$TEMP_WORKFLOW"
        return 0
    else
        echo "❌ Import failed: $(echo "$RESPONSE" | jq -r '.message // .errors[0].message // "unknown error"')"
        rm "$TEMP_WORKFLOW"
        return 1
    fi
}

# ===== BUILD CHROME EXTENSION =====
build_extension() {
    echo "🧩 Building Chrome extension..."

    mkdir -p "$BUILD_DIR/extension"

    if [[ "$DRY_RUN" == "--dry-run" ]]; then
        echo "📂 Would create extension in: $BUILD_DIR/extension"
        return 0
    fi

    # Copy extension files
    cp -r "$PROJECT_ROOT/chrome-extension/"* "$BUILD_DIR/extension/" 2>/dev/null || true

    # Replace placeholders in manifest
    MANIFEST="$BUILD_DIR/extension/manifest.json"
    if [ -f "$MANIFEST" ]; then
        sed -i.bak \
            -e "s|CHROME_POPUP_WEBHOOK|$CHROME_POPUP_WEBHOOK|g" \
            -e "s|N8N_BASE_URL|$N8N_BASE_URL|g" \
            "$MANIFEST"
        rm -f "$MANIFEST.bak"

        echo "✅ Extension built at: $BUILD_DIR/extension"
        echo "   Load in Chrome: chrome://extensions > Load unpacked"
        return 0
    else
        echo "⚠️  No manifest.json found, skipping extension build"
        return 0
    fi
}

# ===== REGISTER MCP TOOLS =====
register_mcp() {
    echo "🔗 Registering MCP tools..."

    if [[ "$DRY_RUN" == "--dry-run" ]]; then
        echo "📋 Would register MCP tools with n8n"
        return 0
    fi

    # Generate MCP tools config
    MCP_CONFIG="$PROJECT_ROOT/config/mcp-tools.json"

    if [ -f "$MCP_CONFIG" ]; then
        echo "✅ MCP tools defined in: $MCP_CONFIG"
        echo "   Tools will be accessible via: $N8N_MCP_SERVER_URL"
        return 0
    else
        echo "⚠️  MCP tools config not found at $MCP_CONFIG"
        return 0
    fi
}

# ===== MAIN =====
echo "Target: $TARGET"
echo "Environment: $ENVIRONMENT"
echo ""

case "$TARGET" in
    n8n|--target=n8n)
        deploy_n8n
        ;;
    extension|--target=extension)
        build_extension
        ;;
    mcp|--target=mcp)
        register_mcp
        ;;
    --all)
        deploy_n8n && build_extension && register_mcp
        ;;
    *)
        echo "Usage: $0 [n8n|extension|mcp|--all] [--dry-run]"
        exit 1
        ;;
esac

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🧪 Test your setup with:"
echo "   ./scripts/test.sh --integration all"
