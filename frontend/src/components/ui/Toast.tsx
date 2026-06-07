import { CheckCircle2 } from 'lucide-react';

interface Props {
  message: string;
  action?: {
    label: string;
    href: string;
  };
}

export function Toast({ message, action }: Props) {
  return (
    <div className="toast" role="status">
      <CheckCircle2 size={16} />
      <span>{message}</span>
      {action && (
        <a href={action.href} target="_blank" rel="noreferrer">
          {action.label}
        </a>
      )}
    </div>
  );
}
