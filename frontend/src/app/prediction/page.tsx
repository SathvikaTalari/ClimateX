'use client';

import React from 'react';
import { PredictionTimelineChart } from '../../components/charts/PredictionTimelineChart';
import { EmptyState } from '../../components/common/EmptyState';
import { TrendingUp, Calendar } from 'lucide-react';
import { RoleContextBanner } from '../../components/roles/RoleContextBanner';

export default function FuturePredictionPage() {
  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      <RoleContextBanner />

      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <TrendingUp className="w-6 h-6 text-emerald-600 dark:text-emeraldGlow-400" />
          <span>Future Scenario Projections (2026 - 2060)</span>
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          CMIP6 Shared Socioeconomic Pathways (SSP) climate projections across temperature, rainfall, and sea level.
        </p>
      </div>

      <div className="glass-panel p-6 border border-slate-200 dark:border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Calendar className="w-4 h-4 text-cyan-600 dark:text-cyanGlow-400" />
            <span>Temperature Trajectory Scenarios (°C Anomaly)</span>
          </h2>
          <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">Baseline: Pre-Industrial</span>
        </div>
        <PredictionTimelineChart />
      </div>

      <EmptyState
        title="Awaiting Downscaled Global Climate Model (GCM) Runs"
        description="Local downscaling pipelines (NEX-GDDP-CMIP6) are initializing simulation grid boundaries."
        sensor="NASA NEX-GDDP Cloud Pipeline"
      />
    </div>
  );
}
