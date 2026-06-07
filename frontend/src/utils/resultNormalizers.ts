import {
  AgentName,
  ApiEndpoint,
  ApiInfo,
  DiscoveryResult,
  FieldMapping,
  MappingResult,
  PipelineResults,
  ReportInfo,
  WalkthroughResult,
} from '../types';

type AnyRecord = Record<string, unknown>;

const HTTP_METHODS = new Set(['GET', 'POST', 'PUT', 'PATCH', 'DELETE']);
const FIELD_TYPES = new Set(['string', 'number', 'boolean', 'date', 'object', 'array']);
const TRANSFORMATIONS = new Set(['direct', 'format', 'compute', 'skip', 'split', 'merge']);

function isRecord(value: unknown): value is AnyRecord {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function asRecord(value: unknown): AnyRecord {
  return isRecord(value) ? value : {};
}

function asList(value: unknown): unknown[] {
  if (Array.isArray(value)) return value;
  if (isRecord(value)) {
    for (const key of ['items', 'endpoints', 'mappings', 'steps', 'prerequisites']) {
      if (Array.isArray(value[key])) return value[key] as unknown[];
    }
  }
  return [];
}

export function displayText(value: unknown, fallback = 'Unknown'): string {
  if (value === null || value === undefined) return fallback;
  if (typeof value === 'string') return value.trim() || fallback;
  if (typeof value === 'number' || typeof value === 'bigint') return String(value);
  if (typeof value === 'boolean') return value ? 'true' : 'false';
  if (Array.isArray(value)) {
    const parts = value.map((item) => displayText(item, '')).filter(Boolean);
    return parts.join(', ') || fallback;
  }
  if (isRecord(value)) {
    for (const key of ['name', 'label', 'title', 'type', 'value', 'key', 'method', 'path', 'url', 'baseUrl']) {
      if (key in value) return displayText(value[key], fallback);
    }
    try {
      return JSON.stringify(value);
    } catch {
      return fallback;
    }
  }
  return String(value).trim() || fallback;
}

function normalizeAuth(value: unknown): ApiInfo['auth'] {
  const text = displayText(value, 'API Key').toLowerCase().replace(/[_-]/g, ' ');
  if (text.includes('oauth')) return 'OAuth2';
  if (text.includes('bearer') || text.includes('token')) return 'Bearer Token';
  if (text.includes('basic')) return 'Basic Auth';
  return 'API Key';
}

function normalizeMethod(value: unknown): ApiEndpoint['method'] {
  const text = displayText(value, 'GET').toUpperCase();
  const method = [...HTTP_METHODS].find((item) => text.includes(item));
  return (method ?? 'GET') as ApiEndpoint['method'];
}

function normalizeFieldType(value: unknown): FieldMapping['sourceType'] {
  const text = displayText(value, 'string').toLowerCase();
  return (FIELD_TYPES.has(text) ? text : 'string') as FieldMapping['sourceType'];
}

function normalizeTransformation(value: unknown): FieldMapping['transformation'] {
  const text = displayText(value, 'direct').toLowerCase();
  return (TRANSFORMATIONS.has(text) ? text : 'direct') as FieldMapping['transformation'];
}

function normalizeConfidence(value: unknown): number {
  const numeric = typeof value === 'number' ? value : Number(displayText(value, '0.75').replace('%', ''));
  if (!Number.isFinite(numeric)) return 0.75;
  const confidence = numeric > 1 ? numeric / 100 : numeric;
  return Math.max(0, Math.min(confidence, 1));
}

function normalizeEndpoint(value: unknown): ApiEndpoint {
  const endpoint = asRecord(value);
  let path = displayText(endpoint.path ?? endpoint.url ?? endpoint.route, '/');
  if (path && !path.startsWith('/') && !path.startsWith('http')) path = `/${path}`;

  return {
    path,
    method: normalizeMethod(endpoint.method ?? endpoint.type),
    description: displayText(endpoint.description ?? endpoint.summary, 'Endpoint'),
    params: isRecord(endpoint.params) ? Object.fromEntries(Object.entries(endpoint.params).map(([key, item]) => [key, displayText(item, '')])) : {},
  };
}

function normalizeApiInfo(value: unknown, fallbackName: string): ApiInfo {
  const api = asRecord(value);
  return {
    name: displayText(api.name ?? api.service, fallbackName),
    baseUrl: displayText(api.baseUrl ?? api.base_url ?? api.url, 'Not specified'),
    auth: normalizeAuth(api.auth ?? api.authentication),
    endpoints: asList(api.endpoints).map(normalizeEndpoint),
  };
}

export function normalizeDiscoveryResult(value: unknown): DiscoveryResult {
  const discovery = asRecord(value);
  return {
    source: normalizeApiInfo(discovery.source, 'Source API'),
    target: normalizeApiInfo(discovery.target, 'Target API'),
  };
}

export function normalizeMappingResult(value: unknown): MappingResult {
  const raw = asRecord(value);
  const mappings = asList(raw.mappings || value).map((item): FieldMapping => {
    const mapping = asRecord(item);
    return {
      sourceField: displayText(mapping.sourceField ?? mapping.source_field, 'source.field'),
      sourceType: normalizeFieldType(mapping.sourceType ?? mapping.source_type),
      targetField: displayText(mapping.targetField ?? mapping.target_field, 'target.field'),
      targetType: normalizeFieldType(mapping.targetType ?? mapping.target_type),
      transformation: normalizeTransformation(mapping.transformation),
      confidence: normalizeConfidence(mapping.confidence),
      notes: displayText(mapping.notes ?? mapping.description, ''),
    };
  });

  const unmappedSource = asList(raw.unmappedSource ?? raw.unmapped_source).map((item) => displayText(item, '')).filter(Boolean);
  const unmappedTarget = asList(raw.unmappedTarget ?? raw.unmapped_target).map((item) => displayText(item, '')).filter(Boolean);
  const totalFields = mappings.length + unmappedSource.length + unmappedTarget.length;

  return {
    mappings,
    unmappedSource,
    unmappedTarget,
    totalFields,
    mappedPercent: totalFields > 0 ? Math.round((mappings.length / totalFields) * 100) : 0,
  };
}

export function normalizeWalkthroughResult(value: unknown): WalkthroughResult {
  const raw = asRecord(value);
  return {
    overview: displayText(raw.overview, 'Integration walkthrough'),
    prerequisites: asList(raw.prerequisites).map((item) => {
      const env = asRecord(item);
      return {
        key: displayText(env.key ?? env.name, 'ENV_VAR'),
        description: displayText(env.description, ''),
        required: Boolean(env.required ?? true),
      };
    }),
    steps: asList(raw.steps).map((item, index) => {
      const step = asRecord(item);
      return {
        title: displayText(step.title, `Step ${index + 1}`),
        description: displayText(step.description, ''),
        codeSnippet: displayText(step.codeSnippet ?? step.code_snippet, ''),
      };
    }),
    executionCommand: displayText(raw.executionCommand ?? raw.execution_command, 'python connector.py'),
  };
}

export function normalizeReportInfo(value: unknown): ReportInfo | undefined {
  if (!isRecord(value)) return undefined;
  const fileName = displayText(value.fileName ?? value.file_name, '');
  const url = displayText(value.url, '');
  if (!fileName || !url) return undefined;
  return {
    fileName,
    url,
    pdfUrl: displayText(value.pdfUrl ?? value.pdf_url, `${url}/pdf`),
    path: displayText(value.path, ''),
    generatedAt: displayText(value.generatedAt ?? value.generated_at, ''),
  };
}

export function normalizeAgentResult(agent: AgentName, value: unknown): PipelineResults[AgentName] {
  if (agent === 'discovery') return normalizeDiscoveryResult(value);
  if (agent === 'mapping') return normalizeMappingResult(value);
  if (agent === 'walkthrough') return normalizeWalkthroughResult(value);
  return displayText(value, '');
}

export function normalizePipelineResults(value: unknown): PipelineResults {
  const raw = asRecord(value);
  const results: PipelineResults = {};
  if ('discovery' in raw) results.discovery = normalizeDiscoveryResult(raw.discovery);
  if ('mapping' in raw) results.mapping = normalizeMappingResult(raw.mapping);
  if ('codegen' in raw) results.codegen = displayText(raw.codegen, '');
  if ('review' in raw) results.review = displayText(raw.review, '');
  if ('walkthrough' in raw) results.walkthrough = normalizeWalkthroughResult(raw.walkthrough);
  results.report = normalizeReportInfo(raw.report);
  return results;
}
