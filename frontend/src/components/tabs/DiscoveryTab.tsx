import { Badge } from '../ui/Badge';
import { EmptyState } from '../ui/EmptyState';
import { Network } from 'lucide-react';
import { ApiInfo, DiscoveryResult } from '../../types';

interface Props {
  result?: DiscoveryResult;
  animated?: boolean;
}

function ApiColumn({ api }: { api: ApiInfo }) {
  return (
    <section className="api-column">
      <div className="api-header">
        <div>
          <h3>{api.name}</h3>
          <p>{api.baseUrl}</p>
        </div>
        <Badge tone="neutral">{api.auth}</Badge>
      </div>
      <div className="endpoint-list">
        {(api.endpoints || []).map((endpoint) => (
          <div className="endpoint-row" key={`${endpoint.method}-${endpoint.path}`}>
            <Badge tone={endpoint.method === 'DELETE' ? 'error' : endpoint.method === 'GET' ? 'cyan' : 'success'}>
              {endpoint.method}
            </Badge>
            <div>
              <strong>{endpoint.path}</strong>
              <p>{endpoint.description}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

export function DiscoveryTab({ result, animated }: Props) {
  if (!result || !result.source || !result.target) {
    return (
      <EmptyState
        icon={Network}
        title="Ready to Connect"
        description="Enter the source and target applications above to begin the AI discovery process."
      />
    );
  }

  return (
    <div className="two-column-grid">
      <ApiColumn api={result.source} />
      <ApiColumn api={result.target} />
    </div>
  );
}
