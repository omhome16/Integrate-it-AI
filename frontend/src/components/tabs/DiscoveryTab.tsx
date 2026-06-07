import { Badge } from '../ui/Badge';
import { EmptyState } from '../ui/EmptyState';
import { Network } from 'lucide-react';
import { ApiInfo, DiscoveryResult } from '../../types';
import { displayText } from '../../utils/resultNormalizers';

interface Props {
  result?: DiscoveryResult;
  animated?: boolean;
}

function ApiColumn({ api }: { api: ApiInfo }) {
  const auth = displayText(api.auth, 'API Key');

  return (
    <section className="api-column">
      <div className="api-header">
        <div>
          <h3>{displayText(api.name, 'API')}</h3>
          <p>{displayText(api.baseUrl, 'Not specified')}</p>
        </div>
        <Badge tone="neutral">{auth}</Badge>
      </div>
      <div className="endpoint-list">
        {(api.endpoints || []).map((endpoint, index) => {
          const method = displayText(endpoint.method, 'GET').toUpperCase();
          const path = displayText(endpoint.path, '/');

          return (
            <div className="endpoint-row" key={`${method}-${path}-${index}`}>
              <Badge tone={method === 'DELETE' ? 'error' : method === 'GET' ? 'cyan' : 'success'}>{method}</Badge>
              <div>
                <strong>{path}</strong>
                <p>{displayText(endpoint.description, 'Endpoint')}</p>
              </div>
            </div>
          );
        })}
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
