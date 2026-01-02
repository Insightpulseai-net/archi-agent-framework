/**
 * GenAI Toolbox Client for TypeScript
 * ====================================
 *
 * Client for Google's GenAI Toolbox - a tool-serving control plane for databases.
 *
 * Architecture:
 *   - Toolbox = DB tool plane (handles pooling, auth, observability)
 *   - Workbench-API = Pipeline plane (artifacts, codegen, orchestration)
 *   - VS Code Extension = UX shell (calls both planes)
 *
 * @example
 * ```typescript
 * import { ToolboxClient } from '@insightpulseai/workbench-toolbox';
 *
 * const client = new ToolboxClient('http://localhost:5000');
 *
 * // Load a toolset
 * const tools = await client.loadToolset('explorer');
 *
 * // Execute a tool
 * const result = await client.executeTool('list_schemas');
 * ```
 */

export * from './client';
export * from './types';
