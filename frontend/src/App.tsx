import { useEffect, useState } from 'react';
import { CenterPanel } from './components/layout/CenterPanel';
import { LogPanel } from './components/layout/LogPanel';
import { Sidebar } from './components/layout/Sidebar';
import { InputBar } from './components/input/InputBar';
import { ProgressBar } from './components/ui/ProgressBar';
import { Toast } from './components/ui/Toast';
import { usePipeline } from './hooks/usePipeline';

export default function App() {
  const pipeline = usePipeline();
  const [showToast, setShowToast] = useState(false);
  const report = pipeline.results.report;

  useEffect(() => {
    if (!pipeline.isDone) return;
    setShowToast(true);
    const timeout = window.setTimeout(() => setShowToast(false), 3600);
    return () => window.clearTimeout(timeout);
  }, [pipeline.isDone]);

  return (
    <div className="app-shell">
      <ProgressBar active={pipeline.isRunning} />
      <InputBar isRunning={pipeline.isRunning} onRun={pipeline.run} onReset={pipeline.reset} />

      {pipeline.error && <div className="error-banner">{pipeline.error}</div>}

      <div className="workspace-grid">
        <Sidebar agents={pipeline.agents} activeAgent={pipeline.activeAgent} />
        <CenterPanel
          agents={pipeline.agents}
          results={pipeline.results}
          activeTab={pipeline.activeTab}
          onTabChange={pipeline.setActiveTab}
        />
        <LogPanel logs={pipeline.logs} streams={pipeline.streams} activeAgent={pipeline.activeAgent} />
      </div>

      {showToast && (
        <Toast
          message={report ? `Report saved: ${report.fileName}` : 'Integration pipeline complete'}
          action={report ? { label: 'PDF', href: report.pdfUrl } : undefined}
        />
      )}
    </div>
  );
}
