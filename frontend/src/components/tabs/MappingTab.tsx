import { FieldMappingDiagram } from '../viz/FieldMappingDiagram';
import { Badge } from '../ui/Badge';
import { EmptyState } from '../ui/EmptyState';
import { ArrowLeftRight } from 'lucide-react';
import { DiscoveryResult, MappingResult } from '../../types';

interface Props {
  mapping?: MappingResult;
  discovery?: DiscoveryResult;
  animated?: boolean;
}

export function MappingTab({ mapping, discovery, animated }: Props) {
  if (!mapping || !mapping.mappings || !discovery) {
    return (
      <EmptyState
        icon={ArrowLeftRight}
        title="Awaiting Discovery"
        description="Field mappings will be generated once the APIs have been successfully discovered."
      />
    );
  }

  return (
    <div className="tab-stack">
      <div className="metric-strip">
        <div>
          <span>Mapped</span>
          <strong>{mapping.mappedPercent}%</strong>
        </div>
        <div>
          <span>Fields</span>
          <strong>{mapping.mappings.length}/{mapping.totalFields}</strong>
        </div>
        <div>
          <span>Review</span>
          <strong>{(mapping.unmappedSource || []).length + (mapping.unmappedTarget || []).length}</strong>
        </div>
      </div>

      <FieldMappingDiagram
        mappings={mapping.mappings}
        sourceName={discovery.source.name}
        targetName={discovery.target.name}
      />

      <div className="mapping-table">
        {mapping.mappings.map((item) => (
          <div className="mapping-row" key={`${item.sourceField}-${item.targetField}`}>
            <code>{item.sourceField}</code>
            <span className="mapping-arrow">to</span>
            <code>{item.targetField}</code>
            <Badge tone={item.confidence > 0.85 ? 'success' : item.confidence > 0.7 ? 'neutral' : 'warn'}>
              {Math.round(item.confidence * 100)}%
            </Badge>
          </div>
        ))}
      </div>
    </div>
  );
}
