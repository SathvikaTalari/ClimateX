'use client';

import React from 'react';
import { ShieldCheck } from 'lucide-react';
import { EmptyState } from '../../components/common/EmptyState';
import { RoleContextBanner } from '../../components/roles/RoleContextBanner';

export default function ImpactVerificationPage() {
  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      <RoleContextBanner />

      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <ShieldCheck className="w-6 h-6 text-cyan-600 dark:text-cyanGlow-400" />
          <span>Impact Verification & MRV (Measurement, Reporting, Verification)</span>
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Satellite-verified ground-truth audit trails for carbon sequestration, afforestation, and coastal restoration projects.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-panel p-5 border border-slate-200 dark:border-slate-800 space-y-2">
          <div className="text-[10px] text-slate-500 dark:text-slate-400 font-mono uppercase">Verified Project Sites</div>
          <div className="text-2xl font-extrabold text-cyan-700 dark:text-cyanGlow-400 font-mono">148 Sites</div>
          <p className="text-xs text-slate-500 dark:text-slate-400">Sentinel-2 change detection verified</p>
        </div>

        <div className="glass-panel p-5 border border-slate-200 dark:border-slate-800 space-y-2">
          <div className="text-[10px] text-slate-500 dark:text-slate-400 font-mono uppercase">Audited Carbon Offset</div>
          <div className="text-2xl font-extrabold text-emerald-600 dark:text-emerald-400 font-mono">4.2M tCO2e</div>
          <p className="text-xs text-slate-500 dark:text-slate-400">Biomass vegetation index validated</p>
        </div>

        <div className="glass-panel p-5 border border-slate-200 dark:border-slate-800 space-y-2">
          <div className="text-[10px] text-slate-500 dark:text-slate-400 font-mono uppercase">Telemetry Proof Standard</div>
          <div className="text-2xl font-extrabold text-amber-600 dark:text-amber-400 font-mono">STAC / ISO 14064</div>
          <p className="text-xs text-slate-500 dark:text-slate-400">Tamper-evident spatial audit records</p>
        </div>
      </div>

      <EmptyState
        title="Awaiting Spatial Verification Ingest Ledger"
        description="Ground-truth drone surveys and Sentinel-1 SAR backscatter verification logs are queuing for cryptographic verification."
        sensor="ClimateX MRV Verification Pipeline"
      />
    </div>
  );
}
