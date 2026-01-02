/**
 * Type definitions for GenAI Toolbox client.
 */

/**
 * Toolbox client configuration options.
 */
export interface ToolboxClientConfig {
  /** Toolbox server URL */
  baseUrl: string;
  /** Request timeout in milliseconds */
  timeout?: number;
  /** Maximum retry attempts */
  maxRetries?: number;
  /** Delay between retries in milliseconds */
  retryDelay?: number;
  /** Optional API key for authentication */
  apiKey?: string;
  /** Custom headers to include in requests */
  headers?: Record<string, string>;
}

/**
 * A tool parameter definition.
 */
export interface ToolParameter {
  /** Parameter name */
  name: string;
  /** Parameter type (string, integer, boolean, etc.) */
  type: string;
  /** Parameter description */
  description?: string;
  /** Whether the parameter is required */
  required?: boolean;
  /** Default value */
  default?: unknown;
}

/**
 * A tool loaded from Toolbox.
 */
export interface ToolboxTool {
  /** Tool name (unique identifier) */
  name: string;
  /** Tool description */
  description: string;
  /** Tool kind (e.g., 'postgres-sql', 'http') */
  kind: string;
  /** Data source name */
  source: string;
  /** Tool parameters */
  parameters: ToolParameter[];
  /** SQL statement template (for SQL tools) */
  statement?: string;
}

/**
 * Toolbox server health response.
 */
export interface HealthResponse {
  status: 'ok' | 'degraded' | 'error';
  version?: string;
  uptime?: number;
}

/**
 * Tool execution result.
 */
export interface ToolExecutionResult<T = unknown> {
  /** Whether execution was successful */
  success: boolean;
  /** Result data */
  data?: T;
  /** Error message if failed */
  error?: string;
  /** Execution time in milliseconds */
  executionTime?: number;
}

/**
 * SQL query result row.
 */
export type SqlRow = Record<string, unknown>;

/**
 * SQL query result.
 */
export interface SqlResult {
  /** Result rows */
  rows: SqlRow[];
  /** Number of rows affected (for write operations) */
  rowCount?: number;
  /** Column metadata */
  columns?: Array<{
    name: string;
    type: string;
  }>;
}

/**
 * Toolbox error with additional context.
 */
export class ToolboxError extends Error {
  constructor(
    message: string,
    public readonly statusCode?: number,
    public readonly toolName?: string,
  ) {
    super(message);
    this.name = 'ToolboxError';
  }
}

/**
 * OpenAI-compatible tool definition.
 * Use this to pass Toolbox tools to OpenAI/LangChain.
 */
export interface OpenAIToolDefinition {
  type: 'function';
  function: {
    name: string;
    description: string;
    parameters: {
      type: 'object';
      properties: Record<string, {
        type: string;
        description?: string;
      }>;
      required: string[];
    };
  };
}

/**
 * Anthropic-compatible tool definition.
 * Use this to pass Toolbox tools to Anthropic Claude.
 */
export interface AnthropicToolDefinition {
  name: string;
  description: string;
  input_schema: {
    type: 'object';
    properties: Record<string, {
      type: string;
      description?: string;
    }>;
    required: string[];
  };
}
