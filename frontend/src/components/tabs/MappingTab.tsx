import { FieldMappingDiagram } from '../viz/FieldMappingDiagram';
import { Badge } from '../ui/Badge';
import { EmptyState } from '../ui/EmptyState';
import { ArrowLeftRight } from 'lucide-react';
import { DiscoveryResult, MappingResult } from '../../types';
import { displayText } from '../../utils/resultNormalizers';

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

  const mappedPercent = Number.isFinite(mapping.mappedPercent) ? mapping.mappedPercent : 0;
  const totalFields = Number.isFinite(mapping.totalFields) ? mapping.totalFields : mapping.mappings.length;

  return (
    <div className="tab-stack">
      <div className="metric-strip">
        <div>
          <span>Mapped</span>
          <strong>{mappedPercent}%</strong>
        </div>
        <div>
          <span>Fields</span>
          <strong>{mapping.mappings.length}/{totalFields}</strong>
        </div>
        <div>
          <span>Review</span>
          <strong>{(mapping.unmappedSource || []).length + (mapping.unmappedTarget || []).length}</strong>
        </div>
      </div>

      <FieldMappingDiagram
        mappings={mapping.mappings}
        sourceName={displayText(discovery.source.name, 'Source')}
        targetName={displayText(discovery.target.name, 'Target')}
      />

      <div className="mapping-table">
        {mapping.mappings.map((item, index) => {
          const sourceField = displayText(item.sourceField, 'source.field');
          const targetField = displayText(item.targetField, 'target.field');
          const confidence = Number.isFinite(item.confidence) ? item.confidence : 0;

          return (
          <div className="mapping-row" key={`${sourceField}-${targetField}-${index}`}>
            <code>{sourceField}</code>
            <span className="mapping-arrow">to</span>
            <code>{targetField}</code>
            <Badge tone={confidence > 0.85 ? 'success' : confidence > 0.7 ? 'neutral' : 'warn'}>
              {Math.round(confidence * 100)}%
            </Badge>
          </div>
          );
        })}
      </div>
    </div>
  );
}
