import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorBannerProps {
  message?: string;
  onRetry?: () => void;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({
  message = 'Failed to load data from ClimateX API.',
  onRetry,
}) => {
  return (
    <div className="glass-panel p-4 border border-rose-300 dark:border-rose-500/30 bg-rose-50/50 dark:bg-rose-950/20 text-rose-700 dark:text-rose-400 flex items-center justify-between rounded-xl">
      <div className="flex items-center gap-3">
        <AlertTriangle className="w-5 h-5 shrink-0" />
        <span className="text-xs font-medium">{message}</span>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-rose-100 dark:bg-rose-500/20 hover:bg-rose-200 dark:hover:bg-rose-500/30 rounded-lg transition-colors border border-rose-300 dark:border-rose-500/30"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retry</span>
        </button>
      )}
    </div>
  );
};
