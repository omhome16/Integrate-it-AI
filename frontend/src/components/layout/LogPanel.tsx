import { Terminal } from 'lucide-react';
import { AgentName, LogEntry } from '../../types';

const LABELS: Record<AgentName | 'system', string> = {
  system: 'system',
  discovery: 'discovery',
  mapping: 'mapping',
  codegen: 'codegen',
  walkthrough: 'walkthrough',
};

interface Props {
  logs: LogEntry[];
  streams: Record<AgentName, string>;
  activeAgent: AgentName | null;
}

export function LogPanel({ logs, streams, activeAgent }: Props) {
  return (
    <aside className="panel log-panel">
      <div className="panel-heading">
        <span>Live Stream</span>
        <Terminal size={15} />
      </div>

      <div className="stream-preview">
        <div className="stream-label">{activeAgent ? `${LABELS[activeAgent]} output` : 'idle'}</div>
        <pre>{activeAgent ? streams[activeAgent] || 'Waiting for tokens...' : 'Ready.'}</pre>
      </div>

      <div className="log-list">
        {logs.length === 0 ? (
          <p className="muted">No events yet.</p>
        ) : (
          logs.map((log) => (
            <div className="log-entry" key={log.id}>
              <span className={`log-agent log-${log.agent}`}>{LABELS[log.agent]}</span>
              <p>{log.message}</p>
            </div>
          ))
        )}
      </div>
    </aside>
  );
}
