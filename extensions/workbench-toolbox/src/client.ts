/**
 * GenAI Toolbox Client Implementation
 * ====================================
 *
 * TypeScript client for Google's GenAI Toolbox server.
 * Provides async interface for loading toolsets and executing database tools.
 *
 * Reference: https://github.com/googleapis/genai-toolbox
 */

import type {
  ToolboxClientConfig,
  ToolboxTool,
  ToolParameter,
  HealthResponse,
  ToolExecutionResult,
  SqlResult,
  OpenAIToolDefinition,
  AnthropicToolDefinition,
} from './types';
import { ToolboxError } from './types';

const DEFAULT_CONFIG: Required<Omit<ToolboxClientConfig, 'apiKey' | 'headers'>> = {
  baseUrl: 'http://localhost:5000',
  timeout: 30000,
  maxRetries: 3,
  retryDelay: 1000,
};

/**
 * Client for GenAI Toolbox server.
 *
 * @example
 * ```typescript
 * const client = new ToolboxClient('http://localhost:5000');
 *
 * // Load tools from a toolset
 * const tools = await client.loadToolset('explorer');
 *
 * // Execute a tool
 * const result = await client.executeTool('list_schemas');
 *
 * // Execute SQL directly
 * const data = await client.executeSql('SELECT * FROM workbench.users LIMIT 10');
 * ```
 */
export class ToolboxClient {
  private readonly config: Required<Omit<ToolboxClientConfig, 'apiKey' | 'headers'>> & {
    apiKey?: string;
    headers: Record<string, string>;
  };
  private tools: Map<string, ToolboxTool> = new Map();
  private toolsets: Map<string, string[]> = new Map();

  constructor(baseUrlOrConfig: string | ToolboxClientConfig) {
    if (typeof baseUrlOrConfig === 'string') {
      this.config = {
        ...DEFAULT_CONFIG,
        baseUrl: baseUrlOrConfig,
        headers: {},
      };
    } else {
      this.config = {
        ...DEFAULT_CONFIG,
        ...baseUrlOrConfig,
        headers: baseUrlOrConfig.headers ?? {},
      };
    }
  }

  /**
   * Make an HTTP request with retry logic.
   */
  private async request<T>(
    method: string,
    path: string,
    options?: {
      body?: unknown;
      headers?: Record<string, string>;
    },
  ): Promise<T> {
    const url = `${this.config.baseUrl}${path}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...this.config.headers,
      ...options?.headers,
    };

    if (this.config.apiKey) {
      headers['Authorization'] = `Bearer ${this.config.apiKey}`;
    }

    let lastError: Error | undefined;

    for (let attempt = 0; attempt < this.config.maxRetries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

        const response = await fetch(url, {
          method,
          headers,
          body: options?.body ? JSON.stringify(options.body) : undefined,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const text = await response.text();
          throw new ToolboxError(
            `Toolbox request failed: ${text}`,
            response.status,
          );
        }

        return await response.json() as T;
      } catch (error) {
        lastError = error as Error;

        // Don't retry on client errors (4xx)
        if (error instanceof ToolboxError && error.statusCode && error.statusCode < 500) {
          throw error;
        }

        // Wait before retrying
        if (attempt < this.config.maxRetries - 1) {
          await this.sleep(this.config.retryDelay * (attempt + 1));
        }
      }
    }

    throw lastError ?? new ToolboxError('Unknown error');
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Check Toolbox server health.
   */
  async health(): Promise<HealthResponse> {
    return this.request<HealthResponse>('GET', '/health');
  }

  /**
   * List all available tools.
   */
  async listTools(): Promise<ToolboxTool[]> {
    const data = await this.request<{ tools: Record<string, Omit<ToolboxTool, 'name'>> }>(
      'GET',
      '/api/tools',
    );

    const tools: ToolboxTool[] = [];
    for (const [name, toolData] of Object.entries(data.tools ?? {})) {
      const tool: ToolboxTool = {
        name,
        description: toolData.description ?? '',
        kind: toolData.kind ?? 'unknown',
        source: toolData.source ?? '',
        parameters: toolData.parameters ?? [],
        statement: toolData.statement,
      };
      tools.push(tool);
      this.tools.set(name, tool);
    }

    return tools;
  }

  /**
   * List all available toolsets.
   */
  async listToolsets(): Promise<Map<string, string[]>> {
    const data = await this.request<{ toolsets: Record<string, string[]> }>(
      'GET',
      '/api/toolsets',
    );

    this.toolsets.clear();
    for (const [name, tools] of Object.entries(data.toolsets ?? {})) {
      this.toolsets.set(name, tools);
    }

    return this.toolsets;
  }

  /**
   * Load a toolset by name.
   *
   * @param toolsetName - Name of the toolset (e.g., "explorer", "analyst")
   * @returns List of tools in the toolset
   */
  async loadToolset(toolsetName: string): Promise<ToolboxTool[]> {
    const data = await this.request<{ tools: ToolboxTool[] }>(
      'GET',
      `/api/toolsets/${toolsetName}`,
    );

    const tools: ToolboxTool[] = [];
    for (const toolData of data.tools ?? []) {
      const tool: ToolboxTool = {
        name: toolData.name ?? '',
        description: toolData.description ?? '',
        kind: toolData.kind ?? 'unknown',
        source: toolData.source ?? '',
        parameters: toolData.parameters ?? [],
        statement: toolData.statement,
      };
      tools.push(tool);
      this.tools.set(tool.name, tool);
    }

    return tools;
  }

  /**
   * Get a specific tool by name.
   */
  async getTool(toolName: string): Promise<ToolboxTool> {
    const cached = this.tools.get(toolName);
    if (cached) {
      return cached;
    }

    const data = await this.request<ToolboxTool>('GET', `/api/tools/${toolName}`);
    const tool: ToolboxTool = {
      name: toolName,
      description: data.description ?? '',
      kind: data.kind ?? 'unknown',
      source: data.source ?? '',
      parameters: data.parameters ?? [],
      statement: data.statement,
    };

    this.tools.set(toolName, tool);
    return tool;
  }

  /**
   * Execute a tool with the given parameters.
   *
   * @param toolName - Name of the tool to execute
   * @param parameters - Tool parameters
   * @returns Tool execution result
   */
  async executeTool<T = unknown>(
    toolName: string,
    parameters?: Record<string, unknown>,
  ): Promise<ToolExecutionResult<T>> {
    try {
      const result = await this.request<ToolExecutionResult<T>>(
        'POST',
        `/api/tools/${toolName}/execute`,
        { body: { parameters: parameters ?? {} } },
      );
      return result;
    } catch (error) {
      if (error instanceof ToolboxError) {
        error.toolName = toolName;
      }
      throw error;
    }
  }

  /**
   * Execute a SQL query via the SQL tool.
   *
   * @param sql - SQL query to execute
   * @param params - Query parameters
   * @param toolName - Name of the SQL tool (default: workbench_sql)
   * @returns Query results
   */
  async executeSql(
    sql: string,
    params?: unknown[],
    toolName: string = 'workbench_sql',
  ): Promise<SqlResult> {
    const parameters: Record<string, unknown> = { sql };
    if (params && params.length > 0) {
      parameters.params = params;
    }

    const result = await this.executeTool<SqlResult>(toolName, parameters);
    return result.data ?? { rows: [] };
  }

  /**
   * Get all loaded tools.
   */
  getLoadedTools(): ToolboxTool[] {
    return Array.from(this.tools.values());
  }

  /**
   * Convert a Toolbox tool to OpenAI function definition.
   */
  toolToOpenAI(tool: ToolboxTool): OpenAIToolDefinition {
    const properties: Record<string, { type: string; description?: string }> = {};
    const required: string[] = [];

    for (const param of tool.parameters) {
      properties[param.name] = {
        type: param.type,
        description: param.description,
      };
      if (param.required) {
        required.push(param.name);
      }
    }

    return {
      type: 'function',
      function: {
        name: tool.name,
        description: tool.description,
        parameters: {
          type: 'object',
          properties,
          required,
        },
      },
    };
  }

  /**
   * Convert a Toolbox tool to Anthropic tool definition.
   */
  toolToAnthropic(tool: ToolboxTool): AnthropicToolDefinition {
    const properties: Record<string, { type: string; description?: string }> = {};
    const required: string[] = [];

    for (const param of tool.parameters) {
      properties[param.name] = {
        type: param.type,
        description: param.description,
      };
      if (param.required) {
        required.push(param.name);
      }
    }

    return {
      name: tool.name,
      description: tool.description,
      input_schema: {
        type: 'object',
        properties,
        required,
      },
    };
  }

  /**
   * Get all loaded tools as OpenAI function definitions.
   */
  getOpenAITools(): OpenAIToolDefinition[] {
    return this.getLoadedTools().map(tool => this.toolToOpenAI(tool));
  }

  /**
   * Get all loaded tools as Anthropic tool definitions.
   */
  getAnthropicTools(): AnthropicToolDefinition[] {
    return this.getLoadedTools().map(tool => this.toolToAnthropic(tool));
  }
}

/**
 * Create a tool executor function for use with agent frameworks.
 *
 * @param client - ToolboxClient instance
 * @returns Async function that executes tools
 *
 * @example
 * ```typescript
 * const client = new ToolboxClient('http://localhost:5000');
 * const executor = createToolExecutor(client);
 *
 * // Use with your agent framework
 * const result = await executor('list_schemas', {});
 * ```
 */
export function createToolExecutor(
  client: ToolboxClient,
): (toolName: string, parameters: Record<string, unknown>) => Promise<unknown> {
  return async (toolName: string, parameters: Record<string, unknown>) => {
    const result = await client.executeTool(toolName, parameters);
    return result.data ?? result;
  };
}
