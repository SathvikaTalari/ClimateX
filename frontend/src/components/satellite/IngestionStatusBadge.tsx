'use client';

import React from 'react';
import { IngestionStatus } from '../../types';
import { Clock, Loader2, CheckCircle2, AlertTriangle } from 'lucide-react';

interface IngestionStatusBadgeProps {
  status: IngestionStatus | string;
  errorText?: string;
  className?: string;
}

export const IngestionStatusBadge: React.FC<IngestionStatusBadgeProps> = ({
  status,
  errorText,
  className = '',
}) => {
  switch (status) {
    case 'pending':
      return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400 border border-amber-300 dark:border-amber-500/30 ${className}`}>
          <Clock className="w-3 h-3 animate-pulse" />
          <span>Pending</span>
        </span>
      );
    case 'processing':
      return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-cyan-100 text-cyan-700 dark:bg-cyanGlow-500/20 dark:text-cyanGlow-400 border border-cyan-300 dark:border-cyanGlow-500/30 ${className}`}>
          <Loader2 className="w-3 h-3 animate-spin" />
          <span>Downloading & Validating</span>
        </span>
      );
    case 'completed':
      return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400 border border-emerald-300 dark:border-emerald-500/30 ${className}`}>
          <CheckCircle2 className="w-3 h-3" />
          <span>Ingested</span>
        </span>
      );
    case 'failed':
      return (
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-100 text-rose-700 dark:bg-rose-500/20 dark:text-rose-400 border border-rose-300 dark:border-rose-500/30 ${className}`}
          title={errorText || 'Ingestion failed'}
        >
          <AlertTriangle className="w-3 h-3" />
          <span>Failed</span>
        </span>
      );
    default:
      return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 ${className}`}>
          {status}
        </span>
      );
  }
};
