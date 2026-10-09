import React from 'react';
import { useClimateStore } from '../../store/useClimateStore';
import { ROLE_INFO } from '../../data/mockData';
import { Info, Sparkles } from 'lucide-react';

export const RoleContextBanner: React.FC = () => {
  const { activeRole } = useClimateStore();
  const info = ROLE_INFO[activeRole];

  return (
    <div className="glass-panel p-4 mb-6 border-l-4 border-l-cyan-500 dark:border-l-cyanGlow-500 flex flex-col md:flex-row md:items-center justify-between gap-3">
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-lg bg-cyan-100 dark:bg-cyanGlow-500/10 border border-cyan-300 dark:border-cyanGlow-500/30 flex items-center justify-center text-cyan-600 dark:text-cyanGlow-400 shrink-0 mt-0.5">
          <Sparkles className="w-4 h-4" />
        </div>
        <div>
          <div className="flex items-center gap-2 mb-0.5">
            <span className="text-xs font-semibold text-slate-700 dark:text-slate-100 tracking-wide uppercase">Active Persona Scope:</span>
            <span className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${info.badgeColor}`}>
              {info.title}
            </span>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
            {info.focusMessage}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2 self-end md:self-auto text-[11px] text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-earth-950/60 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 shrink-0">
        <Info className="w-3.5 h-3.5 text-cyan-600 dark:text-cyanGlow-400" />
        <span>UI adapts to active role</span>
      </div>
    </div>
  );
};
