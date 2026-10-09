'use client';

import React from 'react';
import { RiskRadarChart } from '../../components/charts/RiskRadarChart';
import { EmptyState } from '../../components/common/EmptyState';
import { AlertTriangle, Flame, CloudRain, Waves, Thermometer, ShieldAlert } from 'lucide-react';
import { RoleContextBanner } from '../../components/roles/RoleContextBanner';

export default function ClimateRiskPage() {
  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      <RoleContextBanner />

      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <AlertTriangle className="w-6 h-6 text-rose-500 dark:text-rose-400" />
          <span>Climate Risk & Vulnerability Intelligence</span>
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Spatial hazard risk matrices, compound hazard triggers, and vulnerability exposure index.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-panel p-6 border border-slate-200 dark:border-slate-800 space-y-4">
          <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-rose-500 dark:text-rose-400" />
            <span>Compound Risk Spectrum</span>
          </h2>
          <RiskRadarChart />
        </div>

        <div className="space-y-4">
          <h2 className="text-sm font-bold text-slate-800 dark:text-slate-200">Active Vulnerability Drivers</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="glass-panel p-4 border border-slate-200 dark:border-slate-800 flex items-start gap-3">
              <div className="p-2 rounded-lg bg-rose-100 text-rose-600 border border-rose-200 dark:bg-rose-500/10 dark:text-rose-400 dark:border-rose-500/20">
                <Flame className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-bold text-slate-800 dark:text-slate-200">Wildfire Risk</div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">High canopy moisture deficit</div>
              </div>
            </div>

            <div className="glass-panel p-4 border border-slate-200 dark:border-slate-800 flex items-start gap-3">
              <div className="p-2 rounded-lg bg-blue-100 text-blue-600 border border-blue-200 dark:bg-blue-500/10 dark:text-blue-400 dark:border-blue-500/20">
                <CloudRain className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-bold text-slate-800 dark:text-slate-200">Flash Inundation</div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">Impervious surface overflow</div>
              </div>
            </div>

            <div className="glass-panel p-4 border border-slate-200 dark:border-slate-800 flex items-start gap-3">
              <div className="p-2 rounded-lg bg-cyan-100 text-cyan-600 border border-cyan-200 dark:bg-cyan-500/10 dark:text-cyan-400 dark:border-cyan-500/20">
                <Waves className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-bold text-slate-800 dark:text-slate-200">Coastal Inundation</div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">Storm surge vulnerability</div>
              </div>
            </div>

            <div className="glass-panel p-4 border border-slate-200 dark:border-slate-800 flex items-start gap-3">
              <div className="p-2 rounded-lg bg-amber-100 text-amber-600 border border-amber-200 dark:bg-amber-500/10 dark:text-amber-400 dark:border-amber-500/20">
                <Thermometer className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-bold text-slate-800 dark:text-slate-200">Urban Thermal Stress</div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">High surface heat delta</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <EmptyState
        title="Awaiting High-Resolution Vulnerability Micro-Grid Feed"
        description="Hazard exposure modeling runs on incoming spatial elevation models and population density rasters."
        sensor="GEE / NASA SEDAC Ingestion API"
      />
    </div>
  );
}
