import { AgentState, PipelineResults, TabId } from '../../types';
import { CodeTab } from '../tabs/CodeTab';
import { DiscoveryTab } from '../tabs/DiscoveryTab';
import { MappingTab } from '../tabs/MappingTab';
import { TabBar } from '../tabs/TabBar';
import { WalkthroughTab } from '../tabs/WalkthroughTab';

interface Props {
  agents: AgentState[];
  results: PipelineResults;
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
}

export function CenterPanel({ agents, results, activeTab, onTabChange }: Props) {
  const isRunning = agents.some((a) => a.status === 'running');

  return (
    <main className="panel center-panel">
      <TabBar activeTab={activeTab} onTabChange={onTabChange} agents={agents} />
      <div className="tab-content">
        {activeTab === 'discovery' && <DiscoveryTab result={results.discovery} animated={isRunning} />}
        {activeTab === 'mapping' && <MappingTab mapping={results.mapping} discovery={results.discovery} animated={isRunning} />}
        {activeTab === 'codegen' && <CodeTab code={results.codegen} animated={isRunning} />}
        {activeTab === 'walkthrough' && <WalkthroughTab result={results.walkthrough} animated={isRunning} />}
      </div>
    </main>
  );
}
