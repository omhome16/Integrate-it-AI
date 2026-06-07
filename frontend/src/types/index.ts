export type AgentName = 'discovery' | 'mapping' | 'codegen' | 'walkthrough';
export type AgentStatus = 'idle' | 'running' | 'done' | 'error';
export type TabId = AgentName;

export interface AgentState {
  name: AgentName;
  status: AgentStatus;
  elapsedMs: number;
  startedAt?: number;
}

export interface LogEntry {
  id: string;
  agent: AgentName | 'system';
  message: string;
  timestamp: number;
}

export interface SSEEvent {
  type: 'agent_start' | 'agent_token' | 'agent_done' | 'agent_error' | 'pipeline_done' | 'log';
  agent: AgentName;
  data?: any;
  timestamp: number;
}

export interface ApiEndpoint {
  path: string;
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  description: string;
  params?: Record<string, string>;
}

export interface ApiInfo {
  name: string;
  baseUrl: string;
  auth: 'OAuth2' | 'API Key' | 'Bearer Token' | 'Basic Auth';
  endpoints: ApiEndpoint[];
}

export interface DiscoveryResult {
  source: ApiInfo;
  target: ApiInfo;
}

export interface FieldMapping {
  sourceField: string;
  sourceType: 'string' | 'number' | 'boolean' | 'date' | 'object' | 'array';
  targetField: string;
  targetType: 'string' | 'number' | 'boolean' | 'date' | 'object' | 'array';
  transformation: 'direct' | 'format' | 'compute' | 'skip' | 'split' | 'merge';
  confidence: number;
  notes: string;
}

export interface MappingResult {
  mappings: FieldMapping[];
  unmappedSource: string[];
  unmappedTarget: string[];
  totalFields: number;
  mappedPercent: number;
}

export interface EnvVar {
  key: string;
  description: string;
  required: boolean;
}

export interface WalkthroughStep {
  title: string;
  description: string;
  codeSnippet: string;
}

export interface WalkthroughResult {
  overview: string;
  prerequisites: EnvVar[];
  steps: WalkthroughStep[];
  executionCommand: string;
}

export interface PipelineResults {
  discovery?: DiscoveryResult;
  mapping?: MappingResult;
  codegen?: string;
  walkthrough?: WalkthroughResult;
}
