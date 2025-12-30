# Microsoft Agent Framework - Comprehensive Catalog

> **Generated:** 2025-12-30
> **Sources:** [GitHub Repository](https://github.com/microsoft/agent-framework) | [Microsoft Learn Documentation](https://learn.microsoft.com/en-us/agent-framework/)

---

## Project Overview

| Attribute | Value |
|-----------|-------|
| **Repository** | https://github.com/microsoft/agent-framework |
| **Documentation** | https://learn.microsoft.com/en-us/agent-framework/ |
| **License** | MIT |
| **Stars** | 6,237 |
| **Forks** | 962 |
| **Contributors** | 96 |
| **Languages** | Python (48.3%), C# (46.4%), TypeScript (4.8%) |

**Description:** A comprehensive, multi-language framework for building, orchestrating, and deploying AI agents and multi-agent workflows with support for Python and .NET.

---

## Repository Structure

```
microsoft/agent-framework/
├── .devcontainer/                 # Development container configuration
├── .github/                       # GitHub workflows and CI/CD templates
│
├── agent-samples/                 # Sample agent implementations
│   ├── Azure/                     # Azure integration samples
│   ├── ChatClient/                # Chat client agent examples
│   ├── Foundry/                   # Foundry platform samples
│   └── OpenAI/                    # OpenAI integration samples
│
├── docs/                          # Documentation and specifications
│   ├── assets/                    # Supporting materials
│   ├── decisions/                 # Architectural Decision Records (ADRs)
│   ├── design/                    # Design documentation
│   ├── features/
│   │   └── durable-agents/        # Durable agents feature docs
│   ├── specs/                     # Technical specifications
│   └── FAQS.md                    # Frequently asked questions
│
├── dotnet/                        # .NET/C# implementation
│   ├── src/                       # Source packages (26 projects)
│   ├── samples/                   # Sample projects
│   ├── tests/                     # Test projects
│   └── nuget/                     # NuGet package configs
│
├── python/                        # Python implementation
│   ├── packages/                  # Individual Python packages (18 packages)
│   ├── samples/                   # Sample implementations
│   ├── docs/                      # Python-specific documentation
│   └── tests/                     # Test suite
│
├── schemas/                       # JSON schemas
│   └── durable-agent-entity-state.json
│
├── workflow-samples/              # Declarative workflow examples
│   ├── CustomerSupport.yaml
│   ├── DeepResearch.yaml
│   ├── Marketing.yaml
│   └── MathChat.yaml
│
├── Configuration Files
│   ├── CONTRIBUTING.md
│   ├── CODE_OF_CONDUCT.md
│   ├── SECURITY.md
│   ├── SUPPORT.md
│   ├── COMMUNITY.md
│   ├── TRANSPARENCY_FAQ.md
│   ├── LICENSE
│   └── README.md
```

---

## Python Implementation

### Package Inventory

```
python/packages/
├── core/                  # Core framework functionality
├── a2a/                   # Agent-to-Agent communication
├── ag-ui/                 # Agent UI framework
├── anthropic/             # Anthropic models integration
├── azure-ai/              # Azure AI integration
├── azure-ai-search/       # Azure AI Search integration
├── azurefunctions/        # Azure Functions hosting
├── bedrock/               # AWS Bedrock integration
├── chatkit/               # Chat kit utilities
├── copilotstudio/         # Microsoft Copilot Studio integration
├── declarative/           # Declarative workflow support
├── devui/                 # Development UI tools
├── foundry_local/         # Local foundry support
├── lab/                   # Experimental features
├── mem0/                  # Memory management integration
├── ollama/                # Ollama model support
├── purview/               # Microsoft Purview integration
└── redis/                 # Redis integration
```

### Core Capabilities

| Capability | Description |
|------------|-------------|
| **Agent Types** | Simple Chat, Tool-Enhanced, Multi-Agent, Multimodal |
| **Orchestration** | Sequential, Concurrent, Group Chat, Handoff |
| **Tool Integration** | Native Python functions, OpenAPI specs, MCP |
| **LLM Providers** | OpenAI, Azure OpenAI, Anthropic, AWS Bedrock, Ollama |
| **Streaming** | Real-time async operations |
| **Middleware** | Chat, Agent, Run-level hooks |

### Installation

```bash
# Core framework
pip install agent-framework --pre

# With Azure AI support
pip install agent-framework-azure-ai --pre

# Specific providers
pip install agent-framework[anthropic] --pre
pip install agent-framework[bedrock] --pre

# Laboratory features (experimental)
pip install agent-framework-lab[gaia] --pre
pip install agent-framework-lab[tau2] --pre
```

---

## .NET Implementation

### Package Inventory

```
dotnet/src/
├── Core Layer
│   ├── Microsoft.Agents.AI.Abstractions      # Interface definitions
│   ├── Microsoft.Agents.AI                   # Core implementation
│   └── LegacySupport                         # Backward compatibility
│
├── AI Provider Integrations
│   ├── Microsoft.Agents.AI.OpenAI            # OpenAI models
│   ├── Microsoft.Agents.AI.AzureAI           # Azure OpenAI
│   ├── Microsoft.Agents.AI.AzureAI.Persistent# Persistent Azure AI
│   ├── Microsoft.Agents.AI.Anthropic         # Anthropic Claude
│   └── Microsoft.Agents.AI.CopilotStudio     # Copilot Studio
│
├── Workflow & Orchestration
│   ├── Microsoft.Agents.AI.Workflows                    # Base workflow
│   ├── Microsoft.Agents.AI.Workflows.Declarative        # YAML workflows
│   ├── Microsoft.Agents.AI.Workflows.Declarative.AzureAI# Azure integration
│   └── Microsoft.Agents.AI.DurableTask                  # Durable tasks
│
├── Hosting & Deployment
│   ├── Microsoft.Agents.AI.Hosting                      # Base hosting
│   ├── Microsoft.Agents.AI.Hosting.OpenAI               # OpenAI hosting
│   ├── Microsoft.Agents.AI.Hosting.AzureFunctions       # Serverless
│   ├── Microsoft.Agents.AI.Hosting.A2A                  # A2A hosting
│   ├── Microsoft.Agents.AI.Hosting.A2A.AspNetCore       # ASP.NET Core A2A
│   └── Microsoft.Agents.AI.Hosting.AGUI.AspNetCore      # AGUI hosting
│
├── Data & Storage
│   ├── Microsoft.Agents.AI.CosmosNoSql       # Cosmos DB
│   ├── Microsoft.Agents.AI.Mem0              # Memory management
│   └── Microsoft.Agents.AI.Purview           # Data governance
│
└── UI & Interfaces
    ├── Microsoft.Agents.AI.A2A               # Agent-to-Agent protocol
    ├── Microsoft.Agents.AI.AGUI              # Agent GUI
    ├── Microsoft.Agents.AI.DevUI             # Development UI
    └── Microsoft.Agents.AI.Declarative       # Declarative support
```

### Installation

```bash
# Core framework
dotnet add package Microsoft.Agents.AI

# Azure AI integration
dotnet add package Microsoft.Agents.AI.AzureAI

# Specific providers
dotnet add package Microsoft.Agents.AI.OpenAI
dotnet add package Microsoft.Agents.AI.Anthropic
```

---

## Sample Projects

### .NET Samples (`dotnet/samples/`)

| Sample | Description |
|--------|-------------|
| GettingStarted | Basic usage examples |
| A2AClientServer | Agent-to-Agent client/server |
| AGUIClientServer | Agent GUI client/server |
| AGUIWebChat | Web-based chat with GUI |
| AgentWebChat | Web-based agent chat |
| AzureFunctions | Azure Functions deployment |
| HostedAgents | Self-hosted agent patterns |
| M365Agent | Microsoft 365 integration |

### Python Samples (`python/samples/`)

| Category | Examples |
|----------|----------|
| **agents/** | A2A, Anthropic, Azure, OpenAI, Ollama, CopilotStudio |
| **chat_clients/** | Direct chat client usage patterns |
| **context_providers/** | Mem0, Redis memory management |
| **devui/** | Developer UI examples |
| **evaluation/** | Benchmarking, red teaming |
| **mcp/** | Model Context Protocol |
| **middleware/** | Request/response middleware |
| **multimodal/** | Vision and multimodal capabilities |

### Workflow Samples (`workflow-samples/`)

```yaml
# Declarative YAML-based workflows
├── CustomerSupport.yaml   # Customer service automation
├── DeepResearch.yaml      # Research workflow
├── Marketing.yaml         # Marketing automation
└── MathChat.yaml          # Math collaboration
```

---

## Microsoft Learn Documentation Structure

```
https://learn.microsoft.com/en-us/agent-framework/

Overview/
├── Introduction to Agent Framework
├── Getting Started Guide
└── Quick-Start Tutorial

Tutorials/
├── Create an agent
├── Multi-turn conversations
├── Using functional tools
├── Producing structured output
└── Persisting conversations

User Guides/
├── Implementation guides
├── Best practices
└── Architecture patterns

Migration Guides/
├── Migrate from AutoGen
└── Migrate from Semantic Kernel

API Reference/
├── Python API
└── .NET API
```

---

## Key Features

### Framework Capabilities

| Feature | Description |
|---------|-------------|
| **Graph-based Workflows** | Connect agents and functions using data flows |
| **Streaming Support** | Real-time data processing |
| **Checkpointing** | Persist workflow state for fault tolerance |
| **Human-in-the-Loop** | Pause workflows for human input |
| **Time-Travel Debugging** | Rewind and replay execution |
| **OpenTelemetry** | Distributed tracing and metrics |
| **Middleware Architecture** | Extensible processing pipelines |

### Multi-Agent Orchestration

| Pattern | Description |
|---------|-------------|
| **Sequential** | Execute agents in order with state passing |
| **Concurrent** | Process agents in parallel with aggregation |
| **Group Chat** | Manager-based agent selection |
| **Handoff** | Dynamic routing between agents |

### Declarative Configuration

- YAML-based workflow definitions
- JSON schema validation
- Builder pattern for programmatic construction
- Strong typing with validation

---

## Integration Points

### Cloud Platforms

| Platform | Services |
|----------|----------|
| **Azure** | OpenAI, AI Services, Functions, Cosmos DB, Purview, Cognitive Search |
| **AWS** | Bedrock (foundation models) |
| **OpenAI** | GPT models, Assistants API |
| **Anthropic** | Claude models |

### Data & Memory Systems

| System | Purpose |
|--------|---------|
| **Mem0** | Persistent memory (user profiles, conversation history) |
| **Redis** | Distributed caching, session state |
| **Cosmos DB** | Document storage, NoSQL persistence |
| **Azure AI Search** | Vector search, RAG |
| **Azure Purview** | Data governance, metadata |

### Deployment Targets

| Target | Technologies |
|--------|-------------|
| **Web APIs** | ASP.NET Core, REST |
| **Serverless** | Azure Functions |
| **Chat Platforms** | Copilot Studio |
| **Local** | Python/C# desktop |
| **Distributed** | Service-to-service |

---

## Experimental Features (AF Labs)

| Module | Purpose |
|--------|---------|
| **GAIA** | General assistant benchmark |
| **TAU2** | Customer support benchmark |
| **Lightning** | RL training framework |

> **Warning:** Labs are for experimentation/research only—not recommended for production.

---

## Community & Support

| Resource | Link/Description |
|----------|------------------|
| **Homepage** | https://aka.ms/agent-framework |
| **GitHub** | https://github.com/microsoft/agent-framework |
| **Discord** | Community support and discussion |
| **Office Hours** | Weekly community meetings |
| **Issues** | GitHub Issues for bugs/features |

---

## Quick Start Examples

### Python Example

```python
from agent_framework import Agent, AzureOpenAIChatClient

# Create a chat client
client = AzureOpenAIChatClient(
    azure_endpoint="https://your-endpoint.openai.azure.com",
    api_key="your-api-key",
    model="gpt-4o"
)

# Create an agent
agent = Agent(
    chat_client=client,
    instructions="You are a helpful assistant that writes haiku."
)

# Run the agent
response = await agent.run("Write a haiku about coding")
print(response)
```

### .NET Example

```csharp
using Microsoft.Agents.AI;

// Configure the agent
var agent = new AgentBuilder()
    .WithAzureOpenAI(config.Endpoint, config.ApiKey)
    .WithSystemPrompt("You are a helpful task assistant.")
    .Build();

// Run the agent
var response = await agent.RunAsync("Create a todo list for today");
Console.WriteLine(response);
```

---

## Project Statistics

| Metric | Value |
|--------|-------|
| Repository Size | 46.8 MB |
| Total Commits | 1,149+ |
| Open Issues | 614+ |
| Open PRs | 96+ |
| Contributors | 96 |
| GitHub Stars | 6,237 |
| Forks | 962 |

---

## Related Resources

- **Migration from AutoGen:** [Guide](https://learn.microsoft.com/en-us/agent-framework/migrate-autogen)
- **Migration from Semantic Kernel:** [Guide](https://learn.microsoft.com/en-us/agent-framework/migrate-semantic-kernel)
- **Python samples:** [GitHub](https://github.com/microsoft/agent-framework/tree/main/python/samples)
- **C# samples:** [GitHub](https://github.com/microsoft/agent-framework/tree/main/dotnet/samples)

---

*This catalog is part of the Pulser Agent Framework documentation.*
