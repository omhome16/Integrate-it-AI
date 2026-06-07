import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Render error', error, info);
  }

  render() {
    if (!this.state.error) return this.props.children;

    return (
      <div className="error-boundary" role="alert">
        <div className="empty-state-icon">
          <AlertTriangle size={28} />
        </div>
        <h2>Pipeline view recovered</h2>
        <p>{this.state.error.message}</p>
        <button className="icon-text-button" onClick={() => window.location.reload()}>
          <RotateCcw size={15} />
          Reload
        </button>
      </div>
    );
  }
}
