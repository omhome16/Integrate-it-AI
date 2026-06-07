interface Props {
  active: boolean;
}

export function ProgressBar({ active }: Props) {
  return <div className={`progress-bar ${active ? 'progress-bar-active' : ''}`} />;
}
