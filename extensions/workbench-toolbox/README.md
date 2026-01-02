# @insightpulseai/workbench-toolbox

TypeScript client for [Google GenAI Toolbox](https://github.com/googleapis/genai-toolbox) - a tool-serving control plane for databases.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      VS Code Extension                       │
│                     (UX Shell / Agents)                      │
└────────────────────────┬────────────────────────────────────┘
                         │
           ┌─────────────┴─────────────┐
           │                           │
           ▼                           ▼
┌─────────────────────┐     ┌─────────────────────┐
│   Workbench-API     │     │   GenAI Toolbox     │
│  (Pipeline Plane)   │     │   (DB Tool Plane)   │
│                     │     │                     │
│ - Artifacts         │     │ - Query execution   │
│ - Codegen           │     │ - Schema inspect    │
│ - Orchestration     │     │ - Connection pool   │
│ - Runs              │     │ - OpenTelemetry     │
└─────────────────────┘     └─────────────────────┘
```

## Installation

```bash
npm install @insightpulseai/workbench-toolbox
```

## Quick Start

```typescript
import { ToolboxClient } from '@insightpulseai/workbench-toolbox';

// Create client
const client = new ToolboxClient('http://localhost:5000');

// Load a toolset
const tools = await client.loadToolset('explorer');

// Execute a tool
const result = await client.executeTool('list_schemas');
console.log(result.data);

// Execute SQL directly
const data = await client.executeSql('SELECT * FROM workbench.users LIMIT 10');
console.log(data.rows);
```

## Usage with OpenAI

```typescript
import { ToolboxClient } from '@insightpulseai/workbench-toolbox';
import OpenAI from 'openai';

const toolbox = new ToolboxClient('http://localhost:5000');
const openai = new OpenAI();

// Load toolset and convert to OpenAI format
await toolbox.loadToolset('explorer');
const tools = toolbox.getOpenAITools();

// Use with chat completion
const response = await openai.chat.completions.create({
  model: 'gpt-4',
  messages: [{ role: 'user', content: 'List all database schemas' }],
  tools,
});

// Handle tool calls
for (const toolCall of response.choices[0].message.tool_calls ?? []) {
  const result = await toolbox.executeTool(
    toolCall.function.name,
    JSON.parse(toolCall.function.arguments),
  );
  console.log(result);
}
```

## Usage with Anthropic Claude

```typescript
import { ToolboxClient } from '@insightpulseai/workbench-toolbox';
import Anthropic from '@anthropic-ai/sdk';

const toolbox = new ToolboxClient('http://localhost:5000');
const anthropic = new Anthropic();

// Load toolset and convert to Anthropic format
await toolbox.loadToolset('analyst');
const tools = toolbox.getAnthropicTools();

// Use with Claude
const response = await anthropic.messages.create({
  model: 'claude-3-opus-20240229',
  max_tokens: 1024,
  messages: [{ role: 'user', content: 'Analyze the users table' }],
  tools,
});
```

## Available Toolsets

| Toolset | Description |
|---------|-------------|
| `default` | Core SQL execution tool |
| `explorer` | Read-only data exploration (queries, schema, catalog) |
| `analyst` | Schema analysis and query optimization |
| `workbench` | Platform operations (pipelines, connections, notebooks) |
| `admin` | Full access including write operations |

## API Reference

### `ToolboxClient`

```typescript
class ToolboxClient {
  constructor(baseUrlOrConfig: string | ToolboxClientConfig);

  // Health check
  health(): Promise<HealthResponse>;

  // Tool discovery
  listTools(): Promise<ToolboxTool[]>;
  listToolsets(): Promise<Map<string, string[]>>;
  loadToolset(name: string): Promise<ToolboxTool[]>;
  getTool(name: string): Promise<ToolboxTool>;

  // Tool execution
  executeTool<T>(name: string, params?: Record<string, unknown>): Promise<ToolExecutionResult<T>>;
  executeSql(sql: string, params?: unknown[]): Promise<SqlResult>;

  // Format conversion
  getOpenAITools(): OpenAIToolDefinition[];
  getAnthropicTools(): AnthropicToolDefinition[];
}
```

### Configuration

```typescript
interface ToolboxClientConfig {
  baseUrl: string;         // Toolbox server URL
  timeout?: number;        // Request timeout (ms), default: 30000
  maxRetries?: number;     // Max retry attempts, default: 3
  retryDelay?: number;     // Retry delay (ms), default: 1000
  apiKey?: string;         // Optional API key
  headers?: Record<string, string>;  // Custom headers
}
```

## Development

```bash
# Install dependencies
npm install

# Build
npm run build

# Run tests
npm test

# Type check
npm run typecheck
```

## License

MIT
