import { SUGGESTIONS } from '../../data/demoData';

interface Props {
  disabled: boolean;
  onPick: (source: string, target: string) => void;
}

export function SuggestionChips({ disabled, onPick }: Props) {
  return (
    <div className="suggestion-row">
      {SUGGESTIONS.map((suggestion) => (
        <button
          key={suggestion.label}
          className="chip-button"
          disabled={disabled}
          onClick={() => onPick(suggestion.source, suggestion.target)}
        >
          {suggestion.label}
        </button>
      ))}
    </div>
  );
}
