import type { ReactNode } from 'react';

interface Props {
  children: ReactNode;
  tone?: 'neutral' | 'success' | 'warn' | 'error' | 'cyan';
}

export function Badge({ children, tone = 'neutral' }: Props) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}
