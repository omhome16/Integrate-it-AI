import { useState } from 'react';
import { FieldMapping } from '../../types';
import { displayText } from '../../utils/resultNormalizers';

interface Props {
  mappings: FieldMapping[];
  sourceName: string;
  targetName: string;
}

const FIELD_H = 32;
const FIELD_GAP = 8;
const COL_W = 178;
const SVG_W = 720;
const SRC_X = 24;
const TGT_X = SVG_W - COL_W - 24;

function colorForConfidence(confidence: number) {
  if (confidence >= 0.86) return '#f7f7f7';
  if (confidence >= 0.72) return '#a0a0a0';
  return '#666666';
}

function shortField(value: string) {
  return value.length > 23 ? `${value.slice(0, 22)}...` : value;
}

export function FieldMappingDiagram({ mappings, sourceName, targetName }: Props) {
  const [hovered, setHovered] = useState<number | null>(null);
  const safeMappings = mappings.map((mapping) => ({
    sourceField: displayText(mapping.sourceField, 'source.field'),
    targetField: displayText(mapping.targetField, 'target.field'),
    confidence: Number.isFinite(mapping.confidence) ? mapping.confidence : 0,
  }));
  const sourceFields = [...new Set(safeMappings.map((mapping) => mapping.sourceField))];
  const targetFields = [...new Set(safeMappings.map((mapping) => mapping.targetField))];
  const rows = Math.max(sourceFields.length, targetFields.length, 1);
  const svgH = rows * (FIELD_H + FIELD_GAP) + 72;

  const fieldY = (index: number) => 52 + index * (FIELD_H + FIELD_GAP);
  const fieldCenterY = (index: number) => fieldY(index) + FIELD_H / 2;

  return (
    <div className="mapping-diagram-wrap">
      <svg className="mapping-diagram" viewBox={`0 0 ${SVG_W} ${svgH}`} role="img" aria-label="Field mapping diagram">
        <text className="svg-heading" x={SRC_X + COL_W / 2} y="26" textAnchor="middle">
          {displayText(sourceName, 'Source')}
        </text>
        <text className="svg-heading" x={TGT_X + COL_W / 2} y="26" textAnchor="middle">
          {displayText(targetName, 'Target')}
        </text>

        {sourceFields.map((field, index) => (
          <g key={`source-${field}`}>
            <rect className="field-box" x={SRC_X} y={fieldY(index)} width={COL_W} height={FIELD_H} rx="6" />
            <text className="field-text" x={SRC_X + 12} y={fieldCenterY(index)} dominantBaseline="central">
              {shortField(field)}
            </text>
          </g>
        ))}

        {targetFields.map((field, index) => (
          <g key={`target-${field}`}>
            <rect className="field-box" x={TGT_X} y={fieldY(index)} width={COL_W} height={FIELD_H} rx="6" />
            <text className="field-text" x={TGT_X + 12} y={fieldCenterY(index)} dominantBaseline="central">
              {shortField(field)}
            </text>
          </g>
        ))}

        {safeMappings.map((mapping, index) => {
          const sourceIndex = sourceFields.indexOf(mapping.sourceField);
          const targetIndex = targetFields.indexOf(mapping.targetField);
          const y1 = fieldCenterY(sourceIndex);
          const y2 = fieldCenterY(targetIndex);
          const path = `M ${SRC_X + COL_W} ${y1} C 330 ${y1}, 390 ${y2}, ${TGT_X} ${y2}`;
          const active = hovered === index;

          return (
            <path
              key={`${mapping.sourceField}-${mapping.targetField}`}
              className="mapping-path"
              d={path}
              style={{
                stroke: colorForConfidence(mapping.confidence),
                strokeWidth: active ? 3.2 : 1 + mapping.confidence * 1.4,
                opacity: active ? 1 : 0.58,
                animationDelay: `${index * 0.04}s`,
              }}
              onMouseEnter={() => setHovered(index)}
              onMouseLeave={() => setHovered(null)}
            >
              <title>{`${mapping.sourceField} to ${mapping.targetField} (${Math.round(mapping.confidence * 100)}%)`}</title>
            </path>
          );
        })}
      </svg>
    </div>
  );
}
