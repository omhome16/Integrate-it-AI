import { Code2, GitMerge, BookOpen, Zap, FileText, ShieldCheck } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { AgentName, AgentState, TabId } from '../../types';

const TABS: Array<{ id: TabId; label: string; icon: LucideIcon; agent?: AgentName }> = [
  { id: 'discovery', label: 'Discovery', icon: Zap },
  { id: 'mapping', label: 'Mapping', icon: GitMerge },
  { id: 'codegen', label: 'Code', icon: Code2 },
  { id: 'review', label: 'Review', icon: ShieldCheck },
  { id: 'walkthrough', label: 'Walkthrough', icon: BookOpen },
  { id: 'report', label: 'Report', icon: FileText },
];

interface Props {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  agents: AgentState[];
}

export function TabBar({ activeTab, onTabChange, agents }: Props) {
  const statusByAgent = Object.fromEntries(agents.map((agent) => [agent.name, agent.status])) as Record<AgentName, string>;

  return (
    <div className="tab-bar" role="tablist" aria-label="Pipeline results">
      {TABS.map((tab) => {
        const Icon = tab.icon;
        const status = tab.id === 'report' ? 'idle' : statusByAgent[tab.id] ?? 'idle';
        return (
          <button
            role="tab"
            aria-selected={activeTab === tab.id}
            className={`tab-button ${activeTab === tab.id ? 'tab-active' : ''}`}
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
          >
            <Icon size={14} />
            {tab.label}
            <span className={`tab-dot tab-dot-${status}`} />
          </button>
        );
      })}
    </div>
  );
}
