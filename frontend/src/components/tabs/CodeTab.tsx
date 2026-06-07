import { Copy, Code2 } from 'lucide-react';
import { EmptyState } from '../ui/EmptyState';
import { displayText } from '../../utils/resultNormalizers';

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

  const codeText = displayText(code, '');

  return (
    <div className="code-shell">
      <button className="icon-button copy-button" title="Copy code" onClick={() => navigator.clipboard.writeText(codeText)}>
        <Copy size={15} />
      </button>
      <pre>
        <code>{codeText}</code>
      </pre>
    </div>
  );
}
