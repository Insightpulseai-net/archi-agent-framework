# Bridge Kit CLI Scripts

## Overview

5 production-ready CLI scripts for Bridge Kit setup, deployment, and testing.

## Scripts

### 1. `generate-env.sh` - Environment Template Generator

**Purpose**: Creates `.env.template` and initial `.env` file with all required placeholders.

**Usage**:
```bash
./scripts/generate-env.sh
```

**What it does**:
- Creates `.env.template` with all required variables
- Copies template to `.env` if not exists
- Backs up existing `.env` before overwriting
- Lists all required credentials

**No prerequisites** - safe to run anytime.

---

### 2. `setup-credentials.sh` - Interactive Credential Setup

**Purpose**: Interactively prompts for all credentials and updates `.env`.

**Usage**:
```bash
./scripts/setup-credentials.sh
```

**What it prompts for**:
1. **GitHub App credentials** (App ID, Installation ID, Private Key path, Client ID, Client Secret)
2. **n8n configuration** (Base URL, Webhook URL, API Key)
3. **Chrome extension** (Extension ID, Popup webhook URL)
4. **Repositories** (GitHub org, primary repo, issues repo)
5. **Environment settings** (Environment, debug mode, log level)

**Features**:
- Secure password input (hidden when typing secrets)
- Default values for common settings
- Updates `.env` in-place
- Validates required fields

**Prerequisites**:
- `.env` file must exist (run `generate-env.sh` first)
- Have GitHub App credentials ready
- Have n8n API key ready

---

### 3. `validate.sh` - Credential & API Validation

**Purpose**: Validates all credentials and tests API connectivity.

**Usage**:
```bash
./scripts/validate.sh
```

**What it tests**:
1. ✅ Required files exist (private key)
2. ✅ `.env` variables are configured (no placeholders)
3. ✅ GitHub API is accessible
4. ✅ n8n server is accessible
5. ✅ JWT generation works (GitHub App auth)
6. ✅ GitHub App authentication succeeds
7. ✅ n8n MCP server is reachable

**Output**:
- ✅ Green checkmarks for passing tests
- ❌ Red X for failing tests
- ⚠️ Yellow warnings for optional/skipped tests

**Prerequisites**:
- Completed `.env` file
- `openssl` installed (for JWT generation)
- Network access to GitHub and n8n

---

### 4. `deploy.sh` - Deployment Script

**Purpose**: Deploys workflows to n8n, builds Chrome extension, registers MCP tools.

**Usage**:
```bash
# Deploy everything
./scripts/deploy.sh --all

# Deploy specific target
./scripts/deploy.sh --target n8n
./scripts/deploy.sh --target extension
./scripts/deploy.sh --target mcp

# Dry run (preview changes without executing)
./scripts/deploy.sh --all --dry-run
```

**What it deploys**:

**n8n** (`--target n8n`):
- Reads workflow from `config/bridge-kit-workflow.json`
- Replaces placeholders with `.env` values
- Imports workflow via n8n API
- Returns workflow ID and URL

**Chrome Extension** (`--target extension`):
- Copies files from `chrome-extension/` to `build/extension/`
- Replaces placeholders in `manifest.json`
- Outputs instructions for loading in Chrome

**MCP Tools** (`--target mcp`):
- Validates `config/mcp-tools.json` exists
- Displays MCP server URL
- (Actual registration happens via n8n workflow)

**Prerequisites**:
- Valid `.env` configuration
- n8n API access
- `jq` installed (for JSON processing)
- Workflow template at `config/bridge-kit-workflow.json`

---

### 5. `test.sh` - Integration Tests

**Purpose**: Comprehensive integration tests for all components.

**Usage**:
```bash
# Test everything
./scripts/test.sh --all

# Test specific integration
./scripts/test.sh --integration github
./scripts/test.sh --integration n8n
./scripts/test.sh --integration chrome
./scripts/test.sh --integration mcp
```

**What it tests**:

**GitHub** (`--integration github`):
1. Generates JWT for GitHub App
2. Fetches GitHub App info
3. Gets installation access token
4. Lists accessible repositories
5. Verifies authentication flow

**n8n** (`--integration n8n`):
1. Tests n8n server connectivity
2. Validates API key
3. Lists workflows (if API key valid)
4. Tests webhook endpoint

**Chrome Extension** (`--integration chrome`):
1. Verifies extension ID is configured
2. Provides testing instructions
3. Checks build directory

**MCP Server** (`--integration mcp`):
1. Tests MCP server accessibility
2. Provides testing instructions
3. Verifies MCP URL configuration

**Output**:
- ℹ️ Blue info messages
- ✅ Green success messages
- ❌ Red failure messages (with error details)
- ⚠️ Yellow warnings
- Final summary with pass/fail count

**Exit codes**:
- `0` - All tests passed
- `1` - One or more tests failed

**Prerequisites**:
- Valid `.env` configuration
- `openssl` installed
- `jq` installed
- `curl` installed
- Network access

---

## Installation Workflow

```bash
# 1. Generate environment template
./scripts/generate-env.sh

# 2. Configure credentials (interactive)
./scripts/setup-credentials.sh

# 3. Validate setup
./scripts/validate.sh

# 4. Deploy (dry run first to preview)
./scripts/deploy.sh --all --dry-run
./scripts/deploy.sh --all

# 5. Run integration tests
./scripts/test.sh --all
```

## Common Issues

### `Permission denied`
```bash
chmod +x scripts/*.sh
```

### `.env not found`
```bash
./scripts/generate-env.sh
```

### `jq: command not found`
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt install jq
```

### `openssl: command not found`
```bash
# macOS (should be pre-installed)
which openssl

# Ubuntu/Debian
sudo apt install openssl
```

### GitHub App authentication fails
1. Verify App ID is correct
2. Check private key path is absolute
3. Ensure Installation ID matches your org/account
4. Verify private key permissions: `chmod 600 /path/to/key.pem`

### n8n API returns 401
1. Regenerate API key in n8n
2. Update `.env` with new key
3. Run `./scripts/validate.sh` again

## Script Dependencies

### Required Tools
- `bash` (version 4.0+)
- `curl` - HTTP requests
- `openssl` - JWT generation
- `jq` - JSON parsing
- `sed` - Text replacement
- `base64` - Encoding

### Optional Tools
- `git` - Version control (recommended)
- Chrome browser - For extension testing

## Environment Variable Reference

See `.env.template` for complete list. Key variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_APP_ID` | Yes | GitHub App numeric ID |
| `GITHUB_APP_INSTALLATION_ID` | Yes | Installation ID |
| `GITHUB_APP_PRIVATE_KEY_PATH` | Yes | Absolute path to .pem |
| `GITHUB_APP_CLIENT_ID` | Yes | GitHub App Client ID |
| `GITHUB_APP_CLIENT_SECRET` | Yes | GitHub App secret |
| `N8N_BASE_URL` | Yes | n8n instance URL |
| `N8N_API_KEY` | Yes | n8n API key |
| `N8N_WEBHOOK_URL` | Yes | Webhook endpoint |
| `CHROME_EXTENSION_ID` | No | Chrome extension ID (after build) |
| `GITHUB_ORG` | Yes | GitHub organization |
| `PRIMARY_REPO` | Yes | Main repository |
| `ENVIRONMENT` | No | `development`/`staging`/`production` |

## Security Notes

1. **Never commit `.env`** - It's in `.gitignore`
2. **Protect private keys** - Set permissions: `chmod 600 *.pem`
3. **Rotate secrets regularly** - Regenerate GitHub App secrets quarterly
4. **Use environment-specific keys** - Different keys for dev/staging/prod
5. **Backup `.env` securely** - Encrypted backups only

## Debugging

### Enable debug output
Add to any script:
```bash
set -x  # Print commands before execution
```

### Test individual functions
```bash
# Source the script to access functions
source ./scripts/validate.sh

# Call specific function
pass "Test message"
fail "Error message"
warn "Warning message"
```

### Check generated JWT
```bash
# Run validate.sh and inspect JWT variable
./scripts/validate.sh | grep "JWT generated"
```

### Dry run deployment
```bash
# Preview what would be deployed
./scripts/deploy.sh --all --dry-run
```

## Next Steps

After successful setup:

1. **Explore n8n workflows**: https://n8n.insightpulseai.net
2. **Load Chrome extension**: `chrome://extensions`
3. **Test MCP integration**: Ask Claude to create GitHub issue
4. **Read full documentation**: `../QUICKSTART.md`

## Support

- **Repository**: https://github.com/insightpulseai-net/pulser-agent-framework
- **Issues**: https://github.com/insightpulseai-net/pulser-agent-framework/issues
- **Main docs**: `/QUICKSTART.md`
