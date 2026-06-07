import { AgentCard } from '../agents/AgentCard';
import { AgentName, AgentState } from '../../types';
import { Network, ArrowLeftRight, Code2, Play, LucideIcon } from 'lucide-react';

const AGENT_LABELS: Record<AgentName, { label: string; icon: LucideIcon }> = {
  discovery: { label: 'Discover APIs', icon: Network },
  mapping: { label: 'Map fields', icon: ArrowLeftRight },
  codegen: { label: 'Generate code', icon: Code2 },
  walkthrough: { label: 'Walkthrough', icon: Play },
};

interface Props {
  agents: AgentState[];
  activeAgent: AgentName | null;
}

export function Sidebar({ agents, activeAgent }: Props) {
  return (
    <aside className="panel sidebar-panel">
      <div className="panel-heading">
        <span>Agent Pipeline</span>
        <small>{agents.filter((agent) => agent.status === 'done').length}/{agents.length} done</small>
      </div>
      <div className="agent-list">
        {agents.map((agent, index) => (
          <div className="agent-step" key={agent.name}>
            <AgentCard agent={agent} active={activeAgent === agent.name} />
            {index < agents.length - 1 && <span className={`agent-connector ${agent.status === 'done' ? 'connector-done' : ''}`} />}
          </div>
        ))}
      </div>
    </aside>
  );
}
