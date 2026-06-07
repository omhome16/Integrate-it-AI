import { Badge } from '../ui/Badge';
import { EmptyState } from '../ui/EmptyState';
import { BookOpen, Terminal, Key } from 'lucide-react';
import { WalkthroughResult } from '../../types';

interface Props {
  result?: WalkthroughResult;
  animated?: boolean;
}

export function WalkthroughTab({ result, animated }: Props) {
  if (!result || !result.steps) {
    return (
      <EmptyState
        icon={BookOpen}
        title="Awaiting Code Generation"
        description="A comprehensive walkthrough will be generated once the integration code is written."
      />
    );
  }

  return (
    <div className="tab-stack">
      <section className="glass-panel">
        <h3 style={{ marginBottom: '12px' }}>Overview</h3>
        <p style={{ color: 'var(--text-secondary)' }}>{result.overview}</p>
      </section>

      <div className="two-column-grid">
        <section className="glass-panel">
          <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Key size={16} /> Prerequisites
          </h3>
          <div className="endpoint-list">
            {result.prerequisites.map((env) => (
              <div key={env.key} className="endpoint-row">
                <Badge tone={env.required ? 'cyan' : 'neutral'}>{env.key}</Badge>
                <div>
                  <p style={{ fontSize: '0.9rem' }}>{env.description}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="glass-panel">
          <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Terminal size={16} /> Execution
          </h3>
          <div className="code-shell" style={{ height: 'auto', flex: 'none', background: 'var(--bg-inset)' }}>
            <pre>
              <code>{result.executionCommand}</code>
            </pre>
          </div>
        </section>
      </div>

      <section className="glass-panel" style={{ flex: 1, overflowY: 'auto' }}>
        <h3 style={{ marginBottom: '16px' }}>Step-by-Step Logic Breakdown</h3>
        <div className="tab-stack">
          {result.steps.map((step, index) => (
            <div key={index} className="glass-panel" style={{ background: 'var(--bg-inset)', padding: '16px' }}>
              <h4 style={{ marginBottom: '8px' }}>
                {index + 1}. {step.title}
              </h4>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '12px', fontSize: '0.95rem' }}>
                {step.description}
              </p>
              <div className="code-shell" style={{ height: 'auto', flex: 'none', background: 'var(--bg-base)' }}>
                <pre>
                  <code>{step.codeSnippet}</code>
                </pre>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
