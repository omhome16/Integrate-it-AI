import { AgentState, PipelineResults, TabId } from '../../types';
import { Download, FileDown, FileText } from 'lucide-react';
import { CodeTab } from '../tabs/CodeTab';
import { DiscoveryTab } from '../tabs/DiscoveryTab';
import { MappingTab } from '../tabs/MappingTab';
import { ReportTab } from '../tabs/ReportTab';
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
      {results.report && (
        <div className="report-strip">
          <span>
            <FileText size={15} />
            {results.report.fileName}
          </span>
          <div className="report-strip-actions">
            <button className="icon-text-button" onClick={() => onTabChange('report')}>
              <FileText size={14} />
              View
            </button>
            <a className="icon-text-button" href={results.report.url} download={results.report.fileName}>
              <Download size={14} />
              MD
            </a>
            <a className="icon-text-button" href={results.report.pdfUrl} download={results.report.fileName.replace(/\.md$/i, '.pdf')}>
              <FileDown size={14} />
              PDF
            </a>
          </div>
        </div>
      )}
      <div className="tab-content">
        {activeTab === 'discovery' && <DiscoveryTab result={results.discovery} animated={isRunning} />}
        {activeTab === 'mapping' && <MappingTab mapping={results.mapping} discovery={results.discovery} animated={isRunning} />}
        {activeTab === 'codegen' && <CodeTab code={results.codegen} animated={isRunning} />}
        {activeTab === 'review' && <CodeTab code={results.review} animated={isRunning} />}
        {activeTab === 'walkthrough' && <WalkthroughTab result={results.walkthrough} animated={isRunning} />}
        {activeTab === 'report' && <ReportTab report={results.report} />}
      </div>
    </main>
  );
}
