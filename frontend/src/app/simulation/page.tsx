'use client';

import React, { useState } from 'react';
import { Sliders, Play } from 'lucide-react';
import { RoleContextBanner } from '../../components/roles/RoleContextBanner';
import { EmptyState } from '../../components/common/EmptyState';

export default function SimulationPage() {
  const [tempDelta, setTempDelta] = useState<number>(1.5);
  const [deforestRate, setDeforestRate] = useState<number>(2.0);
  const [seaLevel, setSeaLevel] = useState<number>(0.5);

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      <RoleContextBanner />

      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <Sliders className="w-6 h-6 text-amber-500 dark:text-amber-400" />
          <span>What-if Climate Policy Sandbox</span>
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Simulate counterfactual interventions and stress-test regional ecosystem resilience parameters.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Simulation Controls Slider Panel */}
        <div className="glass-panel p-6 border border-slate-200 dark:border-slate-800 space-y-5">
          <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100">Scenario Parameter Sliders</h2>

          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-slate-700 dark:text-slate-300 font-medium">Temperature Anomaly Target</span>
              <span className="text-cyan-600 dark:text-cyanGlow-400 font-mono font-bold">+{tempDelta}°C</span>
            </div>
            <input
              type="range"
              min="1.0"
              max="4.0"
              step="0.1"
              value={tempDelta}
              onChange={(e) => setTempDelta(parseFloat(e.target.value))}
              className="w-full accent-cyan-600 dark:accent-cyanGlow-400 cursor-pointer"
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-slate-700 dark:text-slate-300 font-medium">Annual Deforestation Change</span>
              <span className="text-amber-600 dark:text-amber-400 font-mono font-bold">{deforestRate > 0 ? `-${deforestRate}%` : `${deforestRate}%`}</span>
            </div>
            <input
              type="range"
              min="-5.0"
              max="5.0"
              step="0.5"
              value={deforestRate}
              onChange={(e) => setDeforestRate(parseFloat(e.target.value))}
              className="w-full accent-amber-500 dark:accent-amber-400 cursor-pointer"
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-slate-700 dark:text-slate-300 font-medium">Sea Level Rise Offset</span>
              <span className="text-blue-600 dark:text-blue-400 font-mono font-bold">+{seaLevel} m</span>
            </div>
            <input
              type="range"
              min="0.1"
              max="2.5"
              step="0.1"
              value={seaLevel}
              onChange={(e) => setSeaLevel(parseFloat(e.target.value))}
              className="w-full accent-blue-600 dark:accent-blue-400 cursor-pointer"
            />
          </div>

          <button
            onClick={() => alert('Simulating scenario physics parameters...')}
            className="w-full py-2.5 px-4 rounded-xl text-xs font-semibold bg-cyan-100 dark:bg-cyanGlow-500/20 text-cyan-700 dark:text-cyanGlow-400 border border-cyan-300 dark:border-cyanGlow-500/40 hover:bg-cyan-200 dark:hover:bg-cyanGlow-500/30 flex items-center justify-center gap-2 transition-all shadow-sm dark:shadow-glow-cyan"
          >
            <Play className="w-4 h-4 fill-current" />
            <span>Run Physics Simulation Engine</span>
          </button>
        </div>

        {/* Simulation Output Area */}
        <div className="lg:col-span-2 space-y-4">
          <div className="glass-panel p-6 border border-slate-200 dark:border-slate-800 space-y-3">
            <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100">Counterfactual Simulation Output</h2>
            <EmptyState
              title="Awaiting Physics Engine Execution"
              description="Click 'Run Physics Simulation Engine' to evaluate ecosystem response under selected temperature and sea-level parameters."
              sensor="ClimateX Spatial Physics Sandbox Engine"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
