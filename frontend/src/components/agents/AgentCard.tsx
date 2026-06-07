import { Check, Clock, Code2, GitMerge, BookOpen, ShieldCheck, Zap } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { AgentName, AgentState } from '../../types';

const AGENTS: Record<AgentName, { label: string; description: string; icon: LucideIcon }> = {
  discovery: { label: 'API Discovery', description: 'Endpoints, auth, schema', icon: Zap },
  mapping: { label: 'Field Mapping', description: 'Types and transforms', icon: GitMerge },
  codegen: { label: 'Code Generation', description: 'Python connector', icon: Code2 },
  review: { label: 'Production Review', description: 'Audit and rewrite', icon: ShieldCheck },
  walkthrough: { label: 'Walkthrough', description: 'Execution guide', icon: BookOpen },
};

interface Props {
  agent: AgentState;
  active: boolean;
}

export function AgentCard({ agent, active }: Props) {
  const config = AGENTS[agent.name];
  const Icon = config.icon;

  return (
    <div className={`agent-card agent-${agent.status} ${active ? 'agent-active' : ''}`}>
      <div className="agent-icon">
        {agent.status === 'done' ? <Check size={15} /> : <Icon size={15} />}
      </div>
      <div className="agent-copy">
        <strong>{config.label}</strong>
        <span>{config.description}</span>
      </div>
      <div className="agent-status">
        {agent.status === 'done' ? (
          <>
            <Clock size={11} />
            {(agent.elapsedMs / 1000).toFixed(1)}s
          </>
        ) : (
          agent.status
        )}
      </div>
    </div>
  );
}
