# Bridge Kit Quick Start

## Installation (5 Commands)

```bash
# 1. Generate environment template
./scripts/generate-env.sh

# 2. Configure YOUR credentials interactively
./scripts/setup-credentials.sh

# 3. Validate everything works
./scripts/validate.sh

# 4. Deploy (optional: add --dry-run first)
./scripts/deploy.sh --all

# 5. Test integration
./scripts/test.sh --all
```

## What Each Script Does

### 1. `generate-env.sh`
- Creates `.env.template` with all required placeholders
- Copies to `.env` if it doesn't exist
- **You need**: Nothing - just run it

### 2. `setup-credentials.sh`
- **Interactive** credential setup (prompts for each value)
- Securely reads secrets (passwords hidden)
- Updates `.env` with your values
- **You need**:
  - GitHub App credentials
  - n8n API key
  - Supabase credentials (anon key, service role key, PostgreSQL password)
  - Google Cloud service account JSON (optional, for Docs sync)

### 3. `validate.sh`
- Tests all credentials are set correctly
- Validates GitHub API connectivity
- Generates JWT and tests authentication
- Checks n8n server accessibility
- **You need**: Completed `.env` file

### 4. `deploy.sh`
- Deploys workflow to n8n
- Builds Chrome extension
- Registers MCP tools
- **You need**: Working credentials, n8n API access
- **Options**:
  - `--target n8n` - Deploy only to n8n
  - `--target extension` - Build only Chrome extension
  - `--target mcp` - Register only MCP tools
  - `--all` - Do everything (default)
  - Add `--dry-run` to preview changes

### 5. `test.sh`
- Integration tests for all components
- Tests GitHub API authentication
- Tests n8n workflows
- Verifies Chrome extension setup
- Tests MCP server accessibility
- **Options**:
  - `--integration github` - Test only GitHub
  - `--integration n8n` - Test only n8n
  - `--integration chrome` - Test only extension
  - `--integration mcp` - Test only MCP
  - `--all` - Test everything (default)

## Prerequisites

Before running scripts, ensure you have:

### Required
- **GitHub App** created at https://github.com/settings/apps
  - App ID
  - Installation ID
  - Private key (.pem file)
  - Client ID
  - Client Secret
- **n8n instance** accessible at https://n8n.insightpulseai.net
  - API key
  - Webhook URL configured
- **OpenSSL** installed (for JWT generation)
- **jq** installed (for JSON parsing)
- **curl** installed (for API testing)

### Optional
- Chrome browser (for extension)
- Claude Desktop or Claude.ai (for MCP testing)

## Getting GitHub App Credentials

1. Go to https://github.com/settings/apps
2. Click "New GitHub App" (or use existing)
3. Note down:
   - **App ID**: Found in app settings
   - **Client ID**: Found in app settings
   - **Client Secret**: Generate and copy immediately
4. Click "Generate private key" → Download `.pem` file
5. Install the app on your organization/account
6. Note the **Installation ID** from URL: `https://github.com/settings/installations/{INSTALLATION_ID}`

## Getting n8n Credentials

1. Log into n8n: https://n8n.insightpulseai.net
2. Go to Settings → API
3. Generate new API key
4. Copy immediately (won't be shown again)

## Directory Structure After Setup

```
pulser-agent-framework/
├── scripts/
│   ├── generate-env.sh      ✅ Generates .env template
│   ├── setup-credentials.sh ✅ Interactive setup
│   ├── validate.sh          ✅ Validates credentials
│   ├── deploy.sh            ✅ Deploys everything
│   └── test.sh              ✅ Integration tests
├── config/
│   ├── bridge-kit-workflow.json  (n8n workflow)
│   └── mcp-tools.json            (MCP tool definitions)
├── chrome-extension/
│   ├── manifest.json
│   ├── popup.html
│   └── background.js
├── build/
│   └── extension/           (built extension)
├── .env.template            (template with placeholders)
├── .env                     (YOUR actual credentials)
└── QUICKSTART.md           (this file)
```

## Troubleshooting

### `.env not found`
Run: `./scripts/generate-env.sh`

### `Private key not found`
- Download `.pem` from GitHub App settings
- Update `GITHUB_APP_PRIVATE_KEY_PATH` in `.env`

### `GitHub authentication failed`
- Verify App ID is correct
- Ensure private key path is absolute
- Check Installation ID is from correct org/account

### `n8n not responding`
- Verify URL: https://n8n.insightpulseai.net
- Check API key is valid
- Ensure network access (VPN, firewall)

### `jq: command not found`
Install jq:
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt install jq
```

## Next Steps

After successful setup:

1. **Explore workflows**: https://n8n.insightpulseai.net
2. **Load Chrome extension**: `chrome://extensions` → Load unpacked from `build/extension/`
3. **Test MCP tools**: Ask Claude to create a GitHub issue
4. **Read full docs**: `docs/BRIDGE_KIT.md`

## Quick Commands Reference

```bash
# Initial setup
./scripts/generate-env.sh
./scripts/setup-credentials.sh

# Validation
./scripts/validate.sh

# Deployment (dry run first)
./scripts/deploy.sh --all --dry-run
./scripts/deploy.sh --all

# Testing
./scripts/test.sh --integration github
./scripts/test.sh --integration n8n
./scripts/test.sh --all

# Specific targets
./scripts/deploy.sh --target n8n
./scripts/deploy.sh --target extension
./scripts/deploy.sh --target mcp
```

## Environment Variables Quick Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_APP_ID` | GitHub App numeric ID | `123456` |
| `GITHUB_APP_INSTALLATION_ID` | Installation numeric ID | `789012` |
| `GITHUB_APP_PRIVATE_KEY_PATH` | Absolute path to .pem | `/Users/you/app.pem` |
| `GITHUB_APP_CLIENT_ID` | GitHub App Client ID | `Iv1.abc123def456` |
| `GITHUB_APP_CLIENT_SECRET` | GitHub App secret | `secret_value_here` |
| `N8N_BASE_URL` | n8n instance URL | `https://n8n.insightpulseai.net` |
| `N8N_API_KEY` | n8n API key | `n8n_api_key_here` |
| `N8N_WEBHOOK_URL` | Webhook endpoint | `https://n8n.../webhook/bridge-kit` |
| `GITHUB_ORG` | GitHub organization | `insightpulseai` |
| `PRIMARY_REPO` | Main repository | `pulser-agent-framework` |
| `ENVIRONMENT` | Runtime environment | `development` |

## Support

- **Issues**: https://github.com/insightpulseai-net/pulser-agent-framework/issues
- **Docs**: `/docs/BRIDGE_KIT.md`
- **n8n Workflows**: https://n8n.insightpulseai.net
