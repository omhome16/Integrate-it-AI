import { CheckCircle2 } from 'lucide-react';

interface Props {
  message: string;
}

export function Toast({ message }: Props) {
  return (
    <div className="toast" role="status">
      <CheckCircle2 size={16} />
      {message}
    </div>
  );
}
