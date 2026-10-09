import React from 'react';

interface LoadingSkeletonProps {
  count?: number;
  type?: 'card' | 'list' | 'map';
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  count = 6,
  type = 'card',
}) => {
  if (type === 'card') {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: count }).map((_, idx) => (
          <div
            key={idx}
            className="glass-panel p-5 border border-slate-200 dark:border-slate-800 animate-pulse space-y-4"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-slate-200 dark:bg-slate-800" />
                <div className="space-y-1.5">
                  <div className="w-24 h-4 rounded bg-slate-200 dark:bg-slate-800" />
                  <div className="w-16 h-3 rounded bg-slate-200 dark:bg-slate-800" />
                </div>
              </div>
              <div className="w-16 h-5 rounded bg-slate-200 dark:bg-slate-800" />
            </div>
            <div className="w-full h-10 rounded bg-slate-200 dark:bg-slate-800" />
            <div className="pt-3 border-t border-slate-200 dark:border-slate-800 flex justify-between">
              <div className="w-20 h-4 rounded bg-slate-200 dark:bg-slate-800" />
              <div className="w-12 h-4 rounded bg-slate-200 dark:bg-slate-800" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="w-full h-32 glass-panel p-4 border border-slate-200 dark:border-slate-800 animate-pulse space-y-3">
      <div className="w-1/3 h-4 bg-slate-200 dark:bg-slate-800 rounded" />
      <div className="w-2/3 h-4 bg-slate-200 dark:bg-slate-800 rounded" />
    </div>
  );
};
