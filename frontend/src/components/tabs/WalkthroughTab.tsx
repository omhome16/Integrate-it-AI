import { Badge } from '../ui/Badge';
import { EmptyState } from '../ui/EmptyState';
import { BookOpen, Terminal, Key } from 'lucide-react';
import { WalkthroughResult } from '../../types';
import { displayText } from '../../utils/resultNormalizers';

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

  const prerequisites = result.prerequisites || [];
  const steps = result.steps || [];

  return (
    <div className="tab-stack">
      <section className="glass-panel">
        <h3 style={{ marginBottom: '12px' }}>Overview</h3>
        <p style={{ color: 'var(--text-secondary)' }}>{displayText(result.overview, 'Integration walkthrough')}</p>
      </section>

      <div className="two-column-grid">
        <section className="glass-panel">
          <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Key size={16} /> Prerequisites
          </h3>
          <div className="endpoint-list">
            {prerequisites.map((env, index) => (
              <div key={`${displayText(env.key, 'ENV_VAR')}-${index}`} className="endpoint-row prereq-row">
                <Badge tone={env.required ? 'cyan' : 'neutral'}>{displayText(env.key, 'ENV_VAR')}</Badge>
                <div>
                  <p style={{ fontSize: '0.9rem' }}>{displayText(env.description, '')}</p>
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
              <code>{displayText(result.executionCommand, 'python connector.py')}</code>
            </pre>
          </div>
        </section>
      </div>

      <section className="glass-panel" style={{ flex: 1, overflowY: 'auto' }}>
        <h3 style={{ marginBottom: '16px' }}>Step-by-Step Logic Breakdown</h3>
        <div className="tab-stack">
          {steps.map((step, index) => (
            <div key={index} className="glass-panel" style={{ background: 'var(--bg-inset)', padding: '16px' }}>
              <h4 style={{ marginBottom: '8px' }}>
                {index + 1}. {displayText(step.title, `Step ${index + 1}`)}
              </h4>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '12px', fontSize: '0.95rem' }}>
                {displayText(step.description, '')}
              </p>
              <div className="code-shell" style={{ height: 'auto', flex: 'none', background: 'var(--bg-base)' }}>
                <pre>
                  <code>{displayText(step.codeSnippet, '')}</code>
                </pre>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
