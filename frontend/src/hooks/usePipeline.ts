import { useCallback, useRef, useState } from 'react';
import { runPipelineStream } from '../services/pipelineApi';
import { AgentName, AgentState, LogEntry, PipelineResults, SSEEvent, TabId } from '../types';
import { normalizeAgentResult, normalizePipelineResults, normalizeReportInfo } from '../utils/resultNormalizers';

const AGENT_ORDER: AgentName[] = ['discovery', 'mapping', 'codegen', 'review', 'walkthrough'];

const TAB_BY_AGENT: Record<AgentName, TabId> = {
  discovery: 'discovery',
  mapping: 'mapping',
  codegen: 'codegen',
  review: 'review',
  walkthrough: 'walkthrough',
};

const emptyStreams = (): Record<AgentName, string> => ({
  discovery: '',
  mapping: '',
  codegen: '',
  review: '',
  walkthrough: '',
});

function initialAgents(): AgentState[] {
  return AGENT_ORDER.map((name) => ({ name, status: 'idle', elapsedMs: 0 }));
}

function logEntry(agent: AgentName | 'system', message: string): LogEntry {
  return {
    id: `${Date.now()}-${Math.random()}`,
    agent,
    message,
    timestamp: Date.now(),
  };
}

export function usePipeline() {
  const [agents, setAgents] = useState<AgentState[]>(initialAgents);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [streams, setStreams] = useState<Record<AgentName, string>>(emptyStreams);
  const [results, setResults] = useState<PipelineResults>({});
  const [activeTab, setActiveTab] = useState<TabId>('discovery');
  const [activeAgent, setActiveAgent] = useState<AgentName | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isDone, setIsDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const startTimesRef = useRef<Partial<Record<AgentName, number>>>({});

  const addLog = useCallback((agent: AgentName | 'system', message: string) => {
    setLogs((prev) => [...prev, logEntry(agent, message)]);
  }, []);

  const updateAgent = useCallback((name: AgentName, updates: Partial<AgentState>) => {
    setAgents((prev) => prev.map((agent) => (agent.name === name ? { ...agent, ...updates } : agent)));
  }, []);

  const clearState = useCallback(() => {
    startTimesRef.current = {};
    setAgents(initialAgents());
    setLogs([]);
    setStreams(emptyStreams());
    setResults({});
    setActiveTab('discovery');
    setActiveAgent(null);
    setIsRunning(false);
    setIsDone(false);
    setError(null);
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    clearState();
  }, [clearState]);

  const handleEvent = useCallback(
    (event: SSEEvent) => {
      const agent = event.agent;

      if (event.type === 'agent_start') {
        startTimesRef.current[agent] = Date.now();
        setActiveAgent(agent);
        setActiveTab(TAB_BY_AGENT[agent]);
        updateAgent(agent, { status: 'running', startedAt: Date.now(), elapsedMs: 0 });
        addLog(agent, 'Agent started');
        return;
      }

      if (event.type === 'agent_token') {
        const token = event.data?.token ?? '';
        setStreams((prev) => ({ ...prev, [agent]: `${prev[agent]}${token}` }));
        return;
      }

      if (event.type === 'agent_done') {
        const elapsedMs = Date.now() - (startTimesRef.current[agent] ?? Date.now());
        const agentResult = normalizeAgentResult(agent, event.data);
        updateAgent(agent, { status: 'done', elapsedMs });
        setResults((prev) => ({ ...prev, [agent]: agentResult }));
        addLog(agent, `Completed in ${(elapsedMs / 1000).toFixed(1)}s`);
        return;
      }

      if (event.type === 'agent_error') {
        updateAgent(agent, { status: 'error' });
        const message = event.data?.message ?? 'Unknown pipeline error';
        const report = normalizeReportInfo(event.data?.report);
        if (report) {
          setResults((prev) => ({ ...prev, report }));
          setActiveTab('report');
        }
        setError(message);
        setIsRunning(false);
        addLog(agent, `Error: ${message}`);
        return;
      }

      if (event.type === 'log') {
        addLog(agent, event.data?.message ?? '');
        return;
      }

      if (event.type === 'pipeline_done') {
        setResults(normalizePipelineResults(event.data));
        setIsRunning(false);
        setIsDone(true);
        setActiveAgent(null);
        setActiveTab('report');
        addLog('system', 'Pipeline complete');
      }
    },
    [addLog, updateAgent]
  );

  const run = useCallback(
    async (source: string, target: string, prompt: string) => {
      abortRef.current?.abort();
      clearState();
      const controller = new AbortController();
      abortRef.current = controller;
      setIsRunning(true);
      addLog('system', `Starting pipeline for ${source} to ${target}`);

      try {
        await runPipelineStream({ source, target, prompt }, handleEvent, controller.signal);
      } catch (err) {
        if (controller.signal.aborted) return;
        const message = err instanceof Error ? err.message : String(err);
        setError(message);
        setIsRunning(false);
        addLog('system', `Pipeline failed: ${message}`);
      }
    },
    [addLog, clearState, handleEvent]
  );

  return {
    agents,
    logs,
    streams,
    results,
    activeTab,
    activeAgent,
    isRunning,
    isDone,
    error,
    setActiveTab,
    run,
    reset,
  };
}
