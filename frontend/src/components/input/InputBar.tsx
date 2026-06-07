import { Play, RotateCcw, Sparkles } from 'lucide-react';
import { useState } from 'react';
import { SuggestionChips } from './SuggestionChips';

interface Props {
  isRunning: boolean;
  onRun: (source: string, target: string, prompt: string) => void;
  onReset: () => void;
}

function formatPrompt(source: string, target: string) {
  return `Connect ${source} with ${target}`;
}

export function InputBar({ isRunning, onRun, onReset }: Props) {
  const [source, setSource] = useState('');
  const [target, setTarget] = useState('');

  const runPipeline = () => {
    if (!source.trim() || !target.trim() || isRunning) return;
    const prompt = formatPrompt(source, target);
    onRun(source, target, prompt);
  };

  const handleSuggestion = (s: string, t: string) => {
    setSource(s);
    setTarget(t);
    const nextPrompt = formatPrompt(s, t);
    onRun(s, t, nextPrompt);
  };

  return (
    <section className="input-shell">
      <div className="brand-lockup">
        <div className="brand-mark">it</div>
        <div>
          <p className="eyebrow">integrate-it ai</p>
          <h1>Integration pipeline</h1>
        </div>
      </div>

      <div className="command-row">
        <Sparkles size={17} className="input-icon" />
        <input
          value={source}
          disabled={isRunning}
          onChange={(event) => setSource(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') runPipeline();
          }}
          placeholder="Salesforce"
        />
        <span style={{ color: 'var(--text-faint)' }}>to</span>
        <input
          value={target}
          disabled={isRunning}
          onChange={(event) => setTarget(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') runPipeline();
          }}
          placeholder="Shopify"
        />
        <button className="icon-text-button" title="Reset pipeline" onClick={onReset}>
          <RotateCcw size={15} />
          Reset
        </button>
        <button
          className="primary-button"
          disabled={isRunning || !source.trim() || !target.trim()}
          title="Run pipeline"
          onClick={() => runPipeline()}
        >
          <Play size={15} fill="currentColor" />
          {isRunning ? 'Running' : 'Run'}
        </button>
      </div>

      <SuggestionChips disabled={isRunning} onPick={handleSuggestion} />
    </section>
  );
}
