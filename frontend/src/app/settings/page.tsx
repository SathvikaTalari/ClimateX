'use client';

import React from 'react';
import { useClimateStore } from '../../store/useClimateStore';
import { RoleContextBanner } from '../../components/roles/RoleContextBanner';
import { Settings, Shield, Satellite, Server, Sun, Moon } from 'lucide-react';

export default function SettingsPage() {
  const { activeRole, setActiveRole, theme, setTheme, toggleTheme } = useClimateStore();

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      <RoleContextBanner />

      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <Settings className="w-6 h-6 text-slate-600 dark:text-slate-300" />
          <span>Platform Settings & System Health</span>
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Configure visual themes, telemetry feeds, API keys, role permissions, and satellite data ingest pipelines.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Settings Configuration */}
        <div className="lg:col-span-2 space-y-6">
          {/* Appearance / Theme Settings */}
          <div className="glass-panel p-6 border border-slate-200 dark:border-slate-800 space-y-4">
            <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <Sun className="w-4 h-4 text-amber-500" />
              <span>Appearance & Color Theme</span>
            </h2>

            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={() => setTheme('light')}
                className={`flex-1 p-4 rounded-xl border flex items-center gap-3 transition-all ${
                  theme === 'light'
                    ? 'bg-cyan-50 border-cyan-500 text-cyan-800 ring-2 ring-cyan-500/20'
                    : 'bg-slate-50 dark:bg-earth-950 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-slate-300'
                }`}
              >
                <div className="w-8 h-8 rounded-lg bg-amber-100 text-amber-600 flex items-center justify-center">
                  <Sun className="w-4 h-4" />
                </div>
                <div className="text-left">
                  <div className="text-xs font-bold">Light Mode</div>
                  <div className="text-[11px] text-slate-500">Clean, crisp high-contrast day palette</div>
                </div>
              </button>

              <button
                onClick={() => setTheme('dark')}
                className={`flex-1 p-4 rounded-xl border flex items-center gap-3 transition-all ${
                  theme === 'dark'
                    ? 'bg-cyan-950/40 border-cyanGlow-500 text-cyanGlow-400 ring-2 ring-cyanGlow-500/20 shadow-glow-cyan'
                    : 'bg-slate-50 dark:bg-earth-950 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-slate-300'
                }`}
              >
                <div className="w-8 h-8 rounded-lg bg-earth-800 text-cyanGlow-400 flex items-center justify-center border border-slate-700">
                  <Moon className="w-4 h-4" />
                </div>
                <div className="text-left">
                  <div className="text-xs font-bold">Dark Mode</div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">Deep Space Earth observation theme</div>
                </div>
              </button>
            </div>
          </div>

          <div className="glass-panel p-6 border border-slate-200 dark:border-slate-800 space-y-4">
            <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <Shield className="w-4 h-4 text-cyan-600 dark:text-cyanGlow-400" />
              <span>Persona & Access Control Configuration</span>
            </h2>

            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Active User Role</label>
              <select
                value={activeRole}
                onChange={(e) => setActiveRole(e.target.value as any)}
                className="w-full bg-white dark:bg-earth-950 border border-slate-300 dark:border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-900 dark:text-slate-100 focus:border-cyan-500 dark:focus:border-cyanGlow-500 focus:outline-none"
              >
                <option value="Citizen">Citizen — Local Climate & Personal Action</option>
                <option value="Government">Government — Macro Risk & Policy Directives</option>
                <option value="Municipality">Municipality — Urban Planning & Infrastructure</option>
                <option value="NGO">NGO — Restoration & Biodiversity Tracking</option>
                <option value="Researcher">Researcher — Multispectral Sensor Data</option>
                <option value="Administrator">Administrator — Platform & Pipeline Operations</option>
              </select>
            </div>
          </div>

          <div className="glass-panel p-6 border border-slate-200 dark:border-slate-800 space-y-4">
            <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <Satellite className="w-4 h-4 text-emerald-600 dark:text-emeraldGlow-400" />
              <span>Satellite Data Provider Endpoints</span>
            </h2>

            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-earth-950/80 rounded-xl border border-slate-200 dark:border-slate-800">
                <div className="flex items-center gap-2.5">
                  <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <div>
                    <div className="font-semibold text-slate-800 dark:text-slate-200">ESA Copernicus Sentinel-2 STAC API</div>
                    <div className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">https://copernicus.stac.climatex.io</div>
                  </div>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400 border border-emerald-300 dark:border-emerald-500/30">Connected</span>
              </div>

              <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-earth-950/80 rounded-xl border border-slate-200 dark:border-slate-800">
                <div className="flex items-center gap-2.5">
                  <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <div>
                    <div className="font-semibold text-slate-800 dark:text-slate-200">USGS Landsat-9 Collection 2 Tier 1</div>
                    <div className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">https://landsat.usgs.gov/stac</div>
                  </div>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400 border border-emerald-300 dark:border-emerald-500/30">Connected</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Col: Admin Node Health */}
        <div className="glass-panel p-6 border border-slate-200 dark:border-slate-800 space-y-4">
          <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Server className="w-4 h-4 text-cyan-600 dark:text-cyanGlow-400" />
            <span>Platform Telemetry Nodes</span>
          </h2>

          <div className="space-y-3 text-xs">
            <div className="p-3 bg-slate-50 dark:bg-earth-950/80 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1">
              <div className="flex justify-between text-slate-700 dark:text-slate-300">
                <span>Tile Server Cluster</span>
                <span className="text-emerald-600 dark:text-emerald-400 font-mono">100% Operational</span>
              </div>
              <div className="w-full h-1.5 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-500 w-full" />
              </div>
            </div>

            <div className="p-3 bg-slate-50 dark:bg-earth-950/80 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1">
              <div className="flex justify-between text-slate-700 dark:text-slate-300">
                <span>STAC Ingestion Pipeline</span>
                <span className="text-cyan-600 dark:text-cyanGlow-400 font-mono">Listening</span>
              </div>
              <div className="w-full h-1.5 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-cyan-500 dark:bg-cyanGlow-400 w-4/5" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
