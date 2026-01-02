# CURSOR DOCUMENTATION: RECURSIVE SURGICAL ANALYSIS

**Analysis Date:** January 2, 2026
**Documentation Source:** https://cursor.com/docs (+ docs.cursor.com mirror)
**Analysis Framework:** AgentIDE competitive intelligence

---

## EXECUTIVE SUMMARY

Cursor has evolved from "VS Code with AI" to an **agent-centric development platform** with Cursor 2.0 (October 2025). The documentation reveals a sophisticated architecture built around:

1. **Composer Model** - Cursor's proprietary frontier coding model (4x faster than comparable models)
2. **Agent-First Interface** - Redesigned UI centered on agents rather than files
3. **Parallel Execution** - Up to 8 concurrent agents via Git worktrees
4. **Context Engine** - Semantic codebase indexing with Turbopuffer vector database
5. **Rules System** - Persistent behavioral instructions (.cursor/rules, AGENTS.md)
6. **MCP Integration** - Model Context Protocol for external tool connections

**Key Insight:** Cursor 2.0 represents a paradigm shift from "AI-assisted coding" to "agent-delegated development" where developers supervise autonomous agents rather than write code directly.

---

## 1. ARCHITECTURAL LAYERS

### 1.1 Four-Tier AI Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      CURSOR ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4: AGENT MODE (Default)                                  │
│  ├── Autonomous task execution                                  │
│  ├── Terminal command execution                                 │
│  ├── Multi-file editing                                         │
│  ├── Web search integration                                     │
│  ├── MCP tool invocation                                        │
│  └── Up to 25 tool calls per turn (continue for more)          │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: EDIT MODE                                             │
│  ├── Single-turn precise edits                                  │
│  ├── Diff preview before apply                                  │
│  └── Focused file modifications                                 │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: ASK MODE                                              │
│  ├── Code exploration                                           │
│  ├── Codebase Q&A                                               │
│  └── Explanations without modification                          │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: TAB COMPLETION                                        │
│  ├── Custom "Fusion" model (proprietary)                        │
│  ├── Multi-line predictions                                     │
│  ├── Cross-file jumping                                         │
│  ├── Auto-imports (TypeScript/Python)                           │
│  └── Intent injection (accept/reject training)                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Composer Interface (Cmd+I)

The unified AI interface combining Ask, Edit, and Agent modes:

| Feature | Ask Mode (Cmd+L) | Edit Mode | Agent Mode (Cmd+I) |
|---------|------------------|-----------|-------------------|
| Purpose | Questions/exploration | Single-turn edits | Autonomous tasks |
| Tools | None | Edit only | All tools |
| Files | Read-only | Single file | Multi-file |
| Terminal | No | No | Yes |
| Web Search | No | No | Yes |
| MCP | No | No | Yes |

**Mode Switching:** Use mode picker or Cmd+. shortcut during conversation.

### 1.3 Layout Options

- **Pane:** Sidebar with chat on left, code editor on right
- **Editor:** Single editor window (movable, splittable, separate window)
- **Floating:** Draggable window positioned anywhere
- **Default Layouts:** agent, editor, zen, browser (Cmd+Opt+Tab to switch)

---

## 2. AGENT SYSTEM DEEP DIVE

### 2.1 Agent Tools (No Limit on Tool Calls)

```yaml
SEARCH TOOLS:
  read_file:
    description: "Reads up to 250 lines (750 in max mode)"
    context: "File content retrieval"

  list_directory:
    description: "Directory structure without content"
    context: "Project navigation"

  codebase_search:
    description: "Semantic search within indexed codebase"
    context: "Conceptual queries"

  grep_search:
    description: "Exact keyword/pattern search"
    context: "Precise matching"

  find_by_name:
    description: "Fuzzy file name matching"
    context: "File discovery"

  web_search:
    description: "Generate and execute web queries"
    context: "External information"

  fetch_rules:
    description: "Retrieve rules by type/description"
    context: "Project conventions"

EDIT TOOLS:
  edit_file:
    description: "Suggest and auto-apply file edits"
    context: "Code modification"

  delete_file:
    description: "Autonomous file deletion (configurable)"
    context: "Cleanup operations"

EXECUTION TOOLS:
  run_terminal:
    description: "Execute commands and monitor output"
    modes:
      - manual_approval: "Requires user confirmation"
      - yolo_mode: "Auto-execute trusted commands"
      - sandboxed: "macOS sandbox with workspace access only"

MCP TOOLS:
  call_mcp_server:
    description: "Invoke external MCP server tools"
    context: "Database, API, documentation access"
```

### 2.2 Agent Workflow (5-Phase Execution)

```
1. COMPREHENSION
   └── Analyze request + codebase context
   └── Identify task requirements and goals

2. DISCOVERY
   └── Search codebase, documentation, web
   └── Identify relevant files and implementations

3. PLANNING
   └── Break task into smaller steps
   └── Plan changes, learn from context

4. EXECUTION
   └── Make code modifications across codebase
   └── Suggest libraries, terminal commands
   └── Steps outside Cursor if needed

5. VALIDATION
   └── Confirm changes look correct
   └── Auto-fix linter errors (when supported)
   └── Create checkpoints for rollback
```

### 2.3 Parallel Agents (Cursor 2.0)

**Mechanism:** Git worktrees for isolated workspaces

```bash
# How Cursor manages parallel agents
my-app/                          # Main workspace
├── .git/                        # Shared repository
├── src/
└── ...

my-app-agent-1/                  # Worktree 1 (Agent A)
├── .git → ../my-app/.git        # Points to main repo
├── src/
└── ...

my-app-agent-2/                  # Worktree 2 (Agent B)
├── .git → ../my-app/.git
├── src/
└── ...
```

**Capabilities:**
- Run up to 8 agents in parallel on single prompt
- Each agent operates in isolated codebase copy
- No file conflicts between agents
- Different models can tackle same problem
- Best solution selected after all complete
- Enable via: `git.showCursorWorktrees` setting

**Use Cases:**
- Same task, multiple approaches (GPT-5 vs Claude Sonnet 4.5 vs Composer)
- Different features in parallel
- A/B testing implementations

### 2.4 Background/Cloud Agents

**Architecture:** Remote VM execution independent of local machine

```
Local Cursor                     Cloud Infrastructure
┌─────────────┐                 ┌─────────────────────┐
│   Editor    │ ─── Trigger ──► │   Cloud Agent VM    │
│             │                 │   ├── Clone repo    │
│   Review    │ ◄── PR/Results  │   ├── Execute task  │
│   Merge     │                 │   └── Create PR     │
└─────────────┘                 └─────────────────────┘
```

**Features:**
- 99.9% reliability, instant startup
- Pro subscription required
- Privacy mode must be disabled (or enterprise config)
- Trigger: Cloud icon in chat or Cmd+E
- Creates PR directly in GitHub for review

**Pricing:** API rates (covered by Pro subscription for basic usage)

---

## 3. CONTEXT ARCHITECTURE

### 3.1 Codebase Indexing Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    INDEXING PIPELINE                            │
├─────────────────────────────────────────────────────────────────┤
│  1. FILE DISCOVERY                                              │
│     └── Scan project, respect .gitignore/.cursorignore          │
│                                                                 │
│  2. CHUNKING                                                    │
│     └── Intelligent code splitting (semantic boundaries)        │
│     └── Function/class-aware chunking                           │
│                                                                 │
│  3. MERKLE TREE SYNC                                            │
│     └── Hash tree for incremental updates                       │
│     └── Only changed files re-uploaded                          │
│                                                                 │
│  4. EMBEDDING GENERATION                                        │
│     └── Custom/OpenAI embedding model                           │
│     └── Vector representations of code chunks                   │
│                                                                 │
│  5. VECTOR STORAGE (Turbopuffer)                                │
│     └── Remote vector database                                  │
│     └── Obfuscated file paths + encrypted chunks                │
│     └── No plaintext code stored for Privacy Mode users         │
│                                                                 │
│  6. QUERY PROCESSING                                            │
│     └── Query embedding computed                                │
│     └── Nearest neighbor search in Turbopuffer                  │
│     └── Obfuscated paths returned to client                     │
│     └── Client reads local files, sends to LLM                  │
│                                                                 │
│  7. CONTEXT ASSEMBLY                                            │
│     └── Relevant chunks assembled                               │
│     └── Sent as context to model                                │
└─────────────────────────────────────────────────────────────────┘
```

**Key Metrics:**
- Search available at 80% index completion
- 5-minute polling for updates
- Cache indexed by chunk hash (shared across team)
- 6 weeks of inactivity → index deletion
- Privacy Mode: No plaintext stored, paths encrypted

### 3.2 @ Symbols (Context Injection)

```yaml
FILE CONTEXT:
  @Files: "Reference specific files"
  @Folders: "Reference entire directories"
  #Files: "Add files without referencing"

CODE CONTEXT:
  @Code: "Reference specific code snippets/symbols"
  @Definitions: "Look up symbol definitions (Inline Edit only)"

DOCUMENTATION:
  @Docs: "Access indexed documentation"
  @Web: "Live web search"
  @Link: "Reference external URLs"

VERSION CONTROL:
  @Git: "Git history, commits, diffs"
  @Recent Changes: "Recent code modifications"

AI/PROJECT:
  @Cursor Rules: "Reference cursor rules"
  @Past Chats: "Summarized composer sessions"
  @Lint Errors: "Current linter errors (Chat only)"
  @Recommended: "Agent auto-pulls relevant context"

COMMANDS:
  /command: "Add open and active files"
```

**Navigation:** Arrow keys to navigate, Enter to select, Ctrl/Cmd M to switch file reading methods.

### 3.3 Context Window Management

| Model | Default Context | Max Context |
|-------|-----------------|-------------|
| Claude 4.5 Opus | 200k | 200k |
| Claude 4.5 Sonnet | 200k | 1M |
| Gemini 3 Flash/Pro | 200k | 1M |
| GPT-5.1/5.2 Codex | 272k | 272k |
| Composer 1 | 200k | 200k |
| Grok Code | 256k | 256k |

**File Reading Limits:**
- Standard: 250 lines per file
- Max Mode: 750 lines per file
- Specific searches: 100 lines max

---

## 4. RULES SYSTEM

### 4.1 Rule Types Hierarchy

```
PRECEDENCE (High → Low):
┌─────────────────────────────────────────────────────────────────┐
│  TEAM RULES (Dashboard-managed, organization-wide)              │
├─────────────────────────────────────────────────────────────────┤
│  PROJECT RULES (.cursor/rules/, version-controlled)             │
├─────────────────────────────────────────────────────────────────┤
│  USER RULES (Global preferences, Cursor Settings)               │
├─────────────────────────────────────────────────────────────────┤
│  AGENTS.md (Simple markdown alternative)                        │
├─────────────────────────────────────────────────────────────────┤
│  .cursorrules (DEPRECATED - use Project Rules)                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Project Rules Anatomy

**Location:** `.cursor/rules/`

```markdown
---
description: "TypeScript API development standards"
globs:
  - "src/api/**/*.ts"
  - "src/services/**/*.ts"
alwaysApply: false
---

# API Development Rules

## Code Style
- Use TypeScript for all new files
- Prefer functional components in React
- Use snake_case for database columns

## Architecture
- Follow the repository pattern
- Keep business logic in service layers

## References
@src/utils/helpers.ts
@src/types/api.d.ts
```

**Metadata Fields:**
- `description`: Human-readable purpose
- `globs`: File patterns for Auto Attached rules
- `alwaysApply`: Always include in context (boolean)

**Rule Application Types:**
1. **Always:** Always included in model context
2. **Auto Attached:** Applied when files match glob patterns
3. **Agent Requested:** Agent can request based on description
4. **Manual:** Only when explicitly referenced

### 4.3 AGENTS.md (Simple Alternative)

**Location:** Project root

```markdown
# Project Instructions

## Code Style
- Use TypeScript for all new files
- Prefer functional components in React
- Use snake_case for database columns

## Architecture
- Follow the repository pattern
- Keep business logic in service layers
```

**Comparison:**
| Feature | Project Rules | AGENTS.md |
|---------|---------------|-----------|
| Metadata | Yes (YAML frontmatter) | No |
| Glob patterns | Yes | No |
| Version controlled | Yes | Yes |
| Complexity | Higher | Simpler |
| Nested rules | Yes | No |

### 4.4 Team Rules (Enterprise)

**Management:** Cursor Dashboard → Team Settings

**Features:**
- Centrally managed by admins
- Automatically applied to all team members
- No local file storage required
- Create deeplinks through Cursor Docs
- Distribute hooks from web dashboard

---

## 5. MODEL CONTEXT PROTOCOL (MCP)

### 5.1 MCP Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP INTEGRATION                              │
├─────────────────────────────────────────────────────────────────┤
│  CURSOR (MCP Client)                                            │
│  └── Supports arbitrary number of MCP servers                   │
│  └── Transports: stdio, SSE, Streamable HTTP                    │
│                                                                 │
│  MCP SERVERS (Tool Providers)                                   │
│  ├── Database servers (PostgreSQL, MongoDB)                     │
│  ├── API servers (GitHub, Stripe, Notion)                       │
│  ├── Documentation servers (Context7)                           │
│  └── Custom servers (any language that prints to stdout)        │
│                                                                 │
│  CAPABILITIES                                                   │
│  ├── Tools: Up to 40 tools from MCP servers                     │
│  ├── Resources: Not yet supported (planned)                     │
│  └── Authentication: Environment variables, OAuth               │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 MCP Configuration

**Location:** `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project)

```json
{
  "mcpServers": {
    "postgres-db": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "postgresql://user:pass@host:5432/db"
      }
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "ghp_xxxx"
      }
    },
    "context7": {
      "url": "https://mcp.context7.com/mcp",
      "headers": {
        "CONTEXT7_API_KEY": "YOUR_API_KEY"
      }
    }
  }
}
```

### 5.3 MCP Tool Usage

**Automatic:** Agent uses relevant MCP tools from Available Tools list

**Explicit:** Tell agent to use specific tool by name or description

**Approval Modes:**
- Manual approval (default): User approves each tool call
- Auto-approval: Configure allowlists for trusted operations

**Limitations:**
- 40 tools maximum from MCP servers
- May not work properly in remote development (SSH)
- Resources not yet supported (tools only)

---

## 6. INLINE EDIT SYSTEM (Cmd+K)

### 6.1 Modes

```yaml
EDIT SELECTION:
  trigger: "Select code + Cmd+K"
  behavior: "Modify selected code based on instructions"
  context: "Includes surrounding code automatically"

GENERATE CODE:
  trigger: "Cmd+K without selection"
  behavior: "Generate new code at cursor position"
  context: "Uses file context for generation"

FULL FILE EDITS:
  trigger: "Cmd+Shift+Enter"
  behavior: "Comprehensive file-wide changes"
  scope: "Entire file modification"

QUICK QUESTION:
  trigger: "Alt+Enter in prompt bar"
  behavior: "Answer questions without generating code"
  followup: "Type 'do it' to convert to code"

SEND TO CHAT:
  trigger: "Cmd+L"
  behavior: "Send selection to Agent for multi-file work"
  scope: "Complex, cross-file operations"
```

### 6.2 Terminal Cmd K

**Location:** Built-in terminal

**Trigger:** Cmd+K opens prompt bar at terminal bottom

**Workflow:**
1. Describe desired action in natural language
2. Cursor generates terminal command
3. Accept with Esc or run immediately with Cmd+Enter

**Context:** Recent terminal history + instructions + @ symbols

---

## 7. TAB COMPLETION (Custom Model)

### 7.1 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TAB MODEL ("Fusion")                         │
├─────────────────────────────────────────────────────────────────┤
│  TYPE: Custom in-house trained model                            │
│  PURPOSE: Fast autocomplete, not general-purpose LLM            │
│  SPEED: Optimized for low-latency predictions                   │
│                                                                 │
│  WORKFLOW:                                                      │
│  1. Client extracts relevant code context                       │
│  2. Context encrypted and sent to backend                       │
│  3. Backend decrypts, Cursor Tab model predicts                 │
│  4. Suggestion returned to client                               │
│                                                                 │
│  LEARNING:                                                      │
│  └── Intent injection via accept (Tab) / reject (Esc)           │
│  └── Model improves with usage patterns                         │
│                                                                 │
│  QUOTA:                                                         │
│  └── Unlimited for Pro/Business users                           │
│  └── Not counted against usage limits                           │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Capabilities

| Feature | Description |
|---------|-------------|
| Multi-line completion | Predicts multiple lines at once |
| Code modification | Can edit existing code, not just insert |
| Cross-file jumping | Predicts next edit location across files |
| Auto-imports | Adds missing imports (TypeScript/Python) |
| Peek view support | Works in Go to Definition views |
| Word-by-word accept | Ctrl+Arrow-Right for partial acceptance |
| Comment-aware | Configurable trigger in comments |

### 7.3 Visual Indicators

- **Ghost text:** Semi-opaque completion suggestions
- **Diff popup:** Shows modifications to existing code
- **Portal window:** Indicates cross-file jump suggestion

---

## 8. BUGBOT (CODE REVIEW)

### 8.1 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    BUGBOT SYSTEM                                │
├─────────────────────────────────────────────────────────────────┤
│  TRIGGERS:                                                      │
│  ├── Automatic: Runs on new PRs (when enabled)                  │
│  ├── Manual: "cursor review" or "bugbot run" comment            │
│  └── Author-only: Only runs on PRs you author                   │
│                                                                 │
│  CAPABILITIES:                                                  │
│  ├── Bug detection                                              │
│  ├── Security issue identification                              │
│  ├── Code quality analysis                                      │
│  └── Fix suggestions with explanations                          │
│                                                                 │
│  INTEGRATION:                                                   │
│  ├── GitHub (including Enterprise Server)                       │
│  ├── GitLab                                                     │
│  └── "Fix in Cursor" button → pre-filled agent prompt           │
│                                                                 │
│  CONFIGURATION:                                                 │
│  └── .cursor/BUGBOT.md files for project-specific context       │
│  └── Nested rules (backend/, api/, frontend/)                   │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 In-Editor Code Review (2.1)

**Feature:** AI code review directly in Cursor

**Access:** Side panel shows issues in your changes

**Workflow:**
1. Make changes
2. AI analyzes diffs
3. Issues appear in sidepanel
4. One-click fixes via agent

---

## 9. CLI AGENT

### 9.1 Installation & Usage

```bash
# Installation
curl https://cursor.com/install -fsSL | bash

# Start CLI with prompt
cursor-agent chat "find one bug and fix it"

# Interactive mode
cursor-agent chat

# MCP management
cursor-agent mcp list
cursor-agent mcp status
```

### 9.2 CLI Capabilities

- Same tools as editor Agent
- Works with any model in subscription
- MCP servers from editor config work in CLI
- Run multiple agents in parallel (terminal)
- Headless execution for CI/CD

---

## 10. SECURITY & PRIVACY

### 10.1 Privacy Modes

| Mode | Data Stored | Training | Use Case |
|------|-------------|----------|----------|
| **Share Data** | Yes | Yes | Help improve Cursor |
| **Privacy Mode** | No | No | Proprietary code |
| **Privacy Mode (Legacy)** | No | No | Existing users |

**Zero Data Retention Agreements:**
- OpenAI
- Anthropic
- Fireworks
- Baseten
- Together

### 10.2 Security Architecture

```yaml
CODEBASE INDEXING:
  - File paths: Obfuscated (split by '/' and '.', encrypted per segment)
  - Code chunks: Encrypted
  - Storage: Turbopuffer (vector DB)
  - Plaintext: Never stored for Privacy Mode users

FILE EXCLUSION:
  - .cursorignore: Exclude from indexing and AI requests
  - .cursorban: Stricter exclusion (planned)
  - Recently viewed files: May still appear in chat context

TERMINAL SECURITY (macOS):
  - Sandboxed terminals: Default in 2.0
  - Sandbox: Read/write workspace only, no internet
  - Allowlisted commands: Bypass sandbox

ENTERPRISE:
  - SOC 2 Type II certified
  - SAML 2.0 SSO
  - SCIM provisioning
  - Team-enforced Privacy Mode (5-minute propagation)
  - Audit logs for admin events
```

### 10.3 Subprocessors

| Provider | Role | Data Exposure |
|----------|------|---------------|
| AWS | Primary infrastructure (US) | Code data |
| Cloudflare | Reverse proxy | Code data |
| Azure | Secondary infrastructure (US) | Code data |
| GCP | Secondary infrastructure | Code data |
| Turbopuffer | Vector database | Embeddings only |
| Fireworks/Baseten/Together | Custom model hosting | Code data (ZDR) |
| OpenAI/Anthropic/Google/xAI | Model providers | Code data (ZDR for Privacy Mode) |

---

## 11. PRICING STRUCTURE

### 11.1 Individual Plans

| Plan | Price | API Usage Included | Bonus |
|------|-------|-------------------|-------|
| Free | $0 | Limited | - |
| Pro | $20/mo | $20 | Yes |
| Pro Plus | $70/mo | $70 | Yes |
| Ultra | $400/mo | $400 | Yes |

### 11.2 Team Plans

| Plan | Price | Features |
|------|-------|----------|
| Teams | $40/user/mo | Admin dashboard, usage stats, SAML/OIDC SSO |
| Enterprise | Custom | Priority support, pooled usage, SCIM, invoicing |

### 11.3 Model Pricing (Per 1M Tokens)

| Model | Input | Cache Write | Cache Read | Output |
|-------|-------|-------------|------------|--------|
| Claude 4.5 Opus | $5.00 | $6.25 | $0.50 | $20.00 |
| Claude 4.5 Sonnet | $1.00 | $1.25 | $0.10 | $4.00 |
| GPT-5.2 | $1.00 | $0.50 | $0.25 | $3.00 |
| Composer 1 | $0.20 | $0.20 | $0.02 | $1.50 |

### 11.4 Usage Estimates

- **Daily Tab users:** Stay within $20
- **Limited Agent users:** Often within $20
- **Daily Agent users:** $60-$100/mo
- **Power users:** $200+/mo

---

## 12. API SURFACE (Enterprise)

### 12.1 Available APIs

```yaml
ADMIN API:
  - Team member management
  - Settings configuration
  - Usage data retrieval
  rate_limit: 20 req/min (60 for spend-limit)

ANALYTICS API:
  - Team usage metrics
  - AI metrics
  - Active users
  - Model usage breakdown
  rate_limit: 100 req/min (team), 50 req/min (by-user)

AI CODE TRACKING API:
  - Commit-level code attribution
  - AI vs human code metrics
  rate_limit: 20 req/min per endpoint

CLOUD AGENTS API (Beta):
  - Programmatic agent creation
  - Agent management
  - Remote execution control

AUTHENTICATION:
  - Basic auth
  - API key format: key_[64 hex chars]
  - Team-scoped keys

CACHING:
  - ETag-based (15-minute window)
  - 304 responses don't count against rate limits
```

---

## 13. COMPOSER MODEL (Cursor 2.0)

### 13.1 Specifications

```yaml
NAME: Composer 1
TYPE: Mixture-of-Experts (MoE)
TRAINING: Reinforcement learning in real codebases
CONTEXT: 200k tokens
SPEED: 250 tokens/second, <30 seconds per task
PERFORMANCE: 4x faster than comparable models

TOOLS TRAINED ON:
  - Semantic search (codebase-wide)
  - File editors
  - Terminal commands
  - Test execution
  - Linter error fixing

CAPABILITIES:
  - Mid-frontier intelligence (approx Claude Haiku 4.5, Gemini Flash 2.5)
  - Below GPT-5, Claude Sonnet 4.5 for complex architecture
  - Optimized for agentic coding
  - Fast iteration suitable for rerunning plans
```

### 13.2 Auto Model Selection

**Feature:** Cursor automatically selects optimal model

**Behavior:**
- Detects performance degradation
- Switches models seamlessly
- No user intervention required

---

## 14. DOCUMENTATION GAPS ANALYSIS

### 14.1 Missing/Incomplete Sections

| Section | Status | Notes |
|---------|--------|-------|
| Agent Chat | 404 | docs.cursor.com/agent → 500 error |
| MCP Details | Sparse | Configuration shown, usage patterns missing |
| Rule Examples | Limited | Few production-ready examples |
| Token Management | Missing | No guidance on context window optimization |
| Error Recovery | Missing | What to do when agents fail |
| Migration Guides | Incomplete | .cursorrules → Project Rules unclear |

### 14.2 Documentation Quality Assessment

**Strengths:**
- Clear feature explanations
- Good keyboard shortcut references
- Transparent pricing
- Privacy/security detailed

**Weaknesses:**
- Scattered across docs.cursor.com and cursor.com/docs
- Some 500 errors on official docs
- Limited cookbook/tutorial content
- No API reference for custom integrations

---

## 15. COMPETITIVE POSITIONING

### 15.1 Cursor vs VS Code + Copilot

| Feature | Cursor | VS Code + Copilot |
|---------|--------|-------------------|
| Architecture | Agent-first | Extension-bolted |
| Codebase Understanding | Semantic indexing | Limited |
| Parallel Agents | 8 concurrent | None |
| Custom Model | Composer + Tab | Copilot only |
| Rules System | Sophisticated | Basic |
| MCP Integration | Native | Via extension |
| Background Agents | Yes (Cloud) | Copilot Workspace (limited) |
| Pricing | Usage-based | Subscription |

### 15.2 Cursor vs Claude Code

| Feature | Cursor | Claude Code |
|---------|--------|-------------|
| Interface | IDE | CLI |
| Multi-model | Yes (8+) | Claude only |
| Tab Completion | Custom model | None |
| Parallel Agents | Git worktrees | Git worktrees |
| Background Agents | Cloud VMs | None |
| Codebase Indexing | Turbopuffer | CLAUDE.md context |
| Visual Review | Full diff UI | Terminal-based |

### 15.3 Key Differentiators

1. **Composer Model:** Proprietary fast coding model
2. **Tab Model:** Custom autocomplete (unlimited for Pro)
3. **Cloud Agents:** Remote execution without local resources
4. **Multi-Model:** No vendor lock-in
5. **Rules System:** Persistent behavioral customization
6. **Parallel Agents:** 8 concurrent via worktrees

---

## 16. AGENTIDE INTEGRATION OPPORTUNITIES

### 16.1 Features to Adopt

| Feature | Priority | Effort | Source |
|---------|----------|--------|--------|
| Rules System | P0 | Medium | .cursor/rules pattern |
| Codebase Indexing | P0 | High | Turbopuffer-style |
| @ Symbols | P0 | Low | Context injection |
| Parallel Agents | P1 | Medium | Git worktree isolation |
| Cloud Agents | P1 | High | Remote VM execution |
| Bugbot Integration | P2 | Medium | PR code review |
| Tab Model | P3 | Very High | Custom autocomplete |

### 16.2 Architecture Patterns

**Context Engine:**
- Merkle tree sync for incremental updates
- Chunk-hash caching for team sharing
- Obfuscated paths for privacy

**Rules Architecture:**
- YAML frontmatter metadata
- Glob-based auto-attachment
- Nested directory rules
- Team dashboard management

**Agent Isolation:**
- Git worktree per agent
- Shared object store
- Isolated index/HEAD
- Safe parallel execution

### 16.3 API Design Inspiration

```typescript
// Cursor-inspired API patterns

interface AgentSession {
  id: string;
  model: ModelType;
  worktree?: string;
  tools: Tool[];
  rules: Rule[];
  context: ContextWindow;
}

interface ContextWindow {
  tokens: number;
  maxTokens: number;
  files: FileContext[];
  symbols: SymbolContext[];
  rules: AppliedRule[];
}

interface Rule {
  path: string;
  type: 'always' | 'auto_attached' | 'agent_requested' | 'manual';
  globs?: string[];
  description?: string;
  content: string;
}

interface Tool {
  name: string;
  type: 'search' | 'edit' | 'terminal' | 'mcp';
  autoApprove: boolean;
  allowlist?: string[];
}
```

---

## 17. CONCLUSION

Cursor 2.0 represents the most mature implementation of agent-centric development available. Key insights:

1. **Agent-First UI:** The paradigm shift from files to agents is complete
2. **Custom Models:** Composer + Tab provide differentiation
3. **Context Engine:** Sophisticated semantic indexing
4. **Rules System:** Persistent behavioral customization
5. **Parallel Execution:** Git worktrees enable safe concurrency
6. **Multi-Model:** No vendor lock-in, model flexibility
7. **Enterprise Ready:** SOC 2, SSO, SCIM, audit logs

**For AgentIDE:** Cursor's architecture provides the blueprint for agent-centric development. Priority adoptions:
- Rules system (.cursor/rules pattern)
- Context engine (semantic indexing)
- Parallel agents (worktree isolation)
- @ symbols (context injection)
- MCP integration (tool ecosystem)

The documentation reveals a product that has moved beyond "AI assistance" to "AI delegation" - developers supervise agents rather than write code directly.

---

*Analysis complete. January 2, 2026*
