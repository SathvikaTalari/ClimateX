import React from 'react';
import { Satellite, Database, Activity, RefreshCw } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  sensor?: string;
  actionText?: string;
  onRetry?: () => void;
  compact?: boolean;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'Awaiting Earth Observation Data',
  description = 'Satellite ingest pipeline actively scanning target coordinates. High-resolution multispectral telemetry will populate upon next pass.',
  sensor = 'Sentinel-2 / Landsat-9 Pipeline',
  actionText,
  onRetry,
  compact = false,
}) => {
  if (compact) {
    return (
      <div className="glass-panel p-4 flex items-center justify-between border-dashed border-slate-300 dark:border-slate-700/60">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-cyan-100 dark:bg-cyanGlow-500/10 border border-cyan-300 dark:border-cyanGlow-500/30 flex items-center justify-center text-cyan-600 dark:text-cyanGlow-400 animate-pulse">
            <Satellite className="w-4 h-4" />
          </div>
          <div>
            <div className="text-sm font-medium text-slate-800 dark:text-slate-200">{title}</div>
            <div className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1.5 mt-0.5">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-amber-500 dark:bg-amber-400 animate-ping" />
              {sensor}
            </div>
          </div>
        </div>
        {onRetry && (
          <button 
            onClick={onRetry}
            className="p-1.5 text-xs text-slate-500 dark:text-slate-400 hover:text-cyan-600 dark:hover:text-cyanGlow-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-md transition-colors"
            title="Poll Sensor Feed"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="glass-panel p-8 text-center border-dashed border-slate-300 dark:border-slate-700/70 flex flex-col items-center justify-center my-4 min-h-[220px]">
      <div className="relative mb-4">
        <div className="w-14 h-14 rounded-2xl bg-slate-100 dark:bg-earth-800 border border-slate-300 dark:border-slate-700 flex items-center justify-center text-cyan-600 dark:text-cyanGlow-400 shadow-md dark:shadow-glow-cyan">
          <Satellite className="w-7 h-7 animate-pulse" />
        </div>
        <div className="absolute -top-1 -right-1 w-4 h-4 bg-amber-500 rounded-full border-2 border-white dark:border-earth-950 flex items-center justify-center">
          <Activity className="w-2.5 h-2.5 text-white dark:text-earth-950" />
        </div>
      </div>

      <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100 mb-1 tracking-wide">
        {title}
      </h3>
      <p className="text-xs text-slate-600 dark:text-slate-400 max-w-md leading-relaxed mb-4">
        {description}
      </p>

      <div className="flex items-center gap-2 bg-slate-100 dark:bg-earth-950/80 px-3 py-1.5 rounded-full border border-slate-300 dark:border-slate-800 text-[11px] text-slate-600 dark:text-slate-400 font-mono">
        <Database className="w-3.5 h-3.5 text-cyan-600 dark:text-cyanGlow-400" />
        <span>Ingest Channel: <strong className="text-slate-800 dark:text-slate-300 font-medium">{sensor}</strong></span>
      </div>

      {actionText && onRetry && (
        <button
          onClick={onRetry}
          className="mt-5 inline-flex items-center gap-2 px-4 py-2 text-xs font-medium bg-cyan-100 dark:bg-cyanGlow-500/10 hover:bg-cyan-200 dark:hover:bg-cyanGlow-500/20 text-cyan-700 dark:text-cyanGlow-400 border border-cyan-300 dark:border-cyanGlow-500/30 rounded-lg transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          {actionText}
        </button>
      )}
    </div>
  );
};
