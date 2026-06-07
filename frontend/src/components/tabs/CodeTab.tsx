import { Copy, Code2 } from 'lucide-react';
import { EmptyState } from '../ui/EmptyState';

interface Props {
  code?: string;
  animated?: boolean;
}

export function CodeTab({ code, animated }: Props) {
  if (!code) {
    return (
      <EmptyState
        icon={Code2}
        title="Awaiting Mappings"
        description="Connector code will be generated once field mappings are established."
      />
    );
  }

  return (
    <div className="code-shell">
      <button className="icon-button copy-button" title="Copy code" onClick={() => navigator.clipboard.writeText(code)}>
        <Copy size={15} />
      </button>
      <pre>
        <code>{code}</code>
      </pre>
    </div>
  );
}
