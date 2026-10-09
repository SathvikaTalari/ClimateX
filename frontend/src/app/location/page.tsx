'use client';

import React, { useState } from 'react';
import { useClimateStore } from '../../store/useClimateStore';
import { LocationSearch } from '../../components/map/LocationSearch';
import { RoleContextBanner } from '../../components/roles/RoleContextBanner';
import { RiskRadarChart } from '../../components/charts/RiskRadarChart';
import { PredictionTimelineChart } from '../../components/charts/PredictionTimelineChart';
import { SatelliteSearchPanel } from '../../components/satellite/SatelliteSearchPanel';
import { EOProcessingPanel } from '../../components/satellite/EOProcessingPanel';
import { AIChangeDetectionPanel } from '../../components/satellite/AIChangeDetectionPanel';
import { MapLibreMap } from '../../components/map/MapLibreMap';
import { RECOMMENDED_ACTIONS } from '../../data/mockData';
import { useLocation } from '../../hooks';
import { EOScene } from '../../types';
import { MapPin, ShieldAlert, CheckCircle2, Activity, ExternalLink } from 'lucide-react';
import Link from 'next/link';

export default function LocationIntelligencePage() {
  const { selectedLocation, activeRole } = useClimateStore();
  const { data: fetchedLocation } = useLocation(selectedLocation.id);
  const activeLocation = fetchedLocation || selectedLocation;

  const [activeFootprint, setActiveFootprint] = useState<EOScene | null>(null);

  // Filter actions for selected location's dominant domain or role relevance
  const roleActions = RECOMMENDED_ACTIONS.filter(
    (act) => act.targetRoles.includes(activeRole) || act.domainId === activeLocation.dominantDomain
  );

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Role Notice */}
      <RoleContextBanner />

      {/* Location Header Overview */}
      <div className="glass-panel p-6 border border-slate-200 dark:border-slate-800 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-cyan-100 text-cyan-700 dark:bg-cyanGlow-500/20 dark:text-cyanGlow-400 border border-cyan-300 dark:border-cyanGlow-500/30">
                {activeLocation.id.toUpperCase()}
              </span>
              <span
                className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
                  activeLocation.riskLevel === 'Severe'
                    ? 'bg-rose-100 text-rose-700 border-rose-300 dark:bg-rose-500/20 dark:text-rose-400 dark:border-rose-500/30'
                    : 'bg-amber-100 text-amber-700 border-amber-300 dark:bg-amber-500/20 dark:text-amber-400 dark:border-amber-500/30'
                }`}
              >
                {activeLocation.riskLevel} Risk Zone
              </span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <MapPin className="w-6 h-6 text-cyan-600 dark:text-cyanGlow-400" />
              <span>{activeLocation.name}</span>
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-mono">
              {activeLocation.region} • {activeLocation.country} | Coordinates: [
              {activeLocation.coordinates[0]}° N, {activeLocation.coordinates[1]}° W]
            </p>
          </div>

          <div className="w-full md:w-80">
            <LocationSearch />
          </div>
        </div>

        {/* Quick Location Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-slate-200 dark:border-slate-800">
          <div className="bg-slate-50 dark:bg-earth-950/80 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
            <div className="text-[10px] text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Landform Type
            </div>
            <div className="text-xs font-bold text-slate-800 dark:text-slate-200 mt-0.5 truncate">
              {activeLocation.landform}
            </div>
          </div>
          <div className="bg-slate-50 dark:bg-earth-950/80 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
            <div className="text-[10px] text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Elevation
            </div>
            <div className="text-xs font-bold text-cyan-700 dark:text-cyanGlow-400 font-mono mt-0.5">
              {activeLocation.elevation}
            </div>
          </div>
          <div className="bg-slate-50 dark:bg-earth-950/80 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
            <div className="text-[10px] text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Dominant Domain
            </div>
            <div className="text-xs font-bold text-emerald-600 dark:text-emerald-400 mt-0.5 capitalize">
              {activeLocation.dominantDomain}
            </div>
          </div>
          <div className="bg-slate-50 dark:bg-earth-950/80 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
            <div className="text-[10px] text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Last Observation
            </div>
            <div className="text-xs font-bold text-slate-700 dark:text-slate-300 font-mono mt-0.5">
              {activeLocation.lastObservation}
            </div>
          </div>
        </div>
      </div>

      {/* Phase 4 Earth Observation MapLibre Interactive Map */}
      <div className="space-y-2">
        <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center justify-between">
          <span className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-cyan-600 dark:text-cyanGlow-400" />
            <span>Interactive Earth Observation Map</span>
          </span>
          {activeFootprint && (
            <span className="text-xs font-mono font-semibold text-cyan-600 dark:text-cyanGlow-400 bg-cyan-100 dark:bg-cyanGlow-500/20 px-2 py-0.5 rounded border border-cyan-300 dark:border-cyanGlow-500/30">
              Active Scene: {activeFootprint.scene_id}
            </span>
          )}
        </h2>
        <MapLibreMap
          height="450px"
          activeFootprint={activeFootprint}
        />
      </div>

      {/* Main Analysis Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Real Satellite EO Catalog Search & Radar Chart (2 Cols) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Phase 4 Earth Observation Real Satellite Search Panel */}
          <SatelliteSearchPanel
            location={activeLocation}
            onFootprintSelect={(scene) => setActiveFootprint(scene)}
          />

          {/* Phase 5A Earth Observation Processing & Feature Statistics Panel */}
          <EOProcessingPanel
            location={activeLocation}
            selectedSceneId={activeFootprint?.scene_id}
          />

          {/* Phase 5B AI Change Detection Panel */}
          <AIChangeDetectionPanel
            location={activeLocation}
          />

          {/* Climate Risk Radar Analysis Chart */}
          <div className="glass-panel p-5 border border-slate-200 dark:border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-500 dark:text-rose-400" />
                <span>Climate Vulnerability Radar</span>
              </h2>
              <span className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                Multivariate Risk Model
              </span>
            </div>
            <RiskRadarChart />
          </div>
        </div>

        {/* Right Column: Future Prediction & Recommended Actions (1 Col) */}
        <div className="space-y-6">
          {/* Scenario Timeline Projection Chart */}
          <div className="glass-panel p-5 border border-slate-200 dark:border-slate-800 space-y-3">
            <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <Activity className="w-4 h-4 text-amber-500 dark:text-amber-400" />
              <span>Climate Scenario Projections</span>
            </h2>
            <PredictionTimelineChart />
          </div>

          {/* Persona Recommended Interventions */}
          <div className="glass-panel p-5 border border-slate-200 dark:border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                <span>Recommended Interventions</span>
              </h2>
              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400 font-semibold border border-emerald-300 dark:border-emerald-500/30">
                {activeRole}
              </span>
            </div>

            <div className="space-y-3">
              {roleActions.length > 0 ? (
                roleActions.map((act) => (
                  <div
                    key={act.id}
                    className="bg-slate-50 dark:bg-earth-950/80 p-3 rounded-xl border border-slate-200 dark:border-slate-800/80 space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                        {act.title}
                      </span>
                      <span className="text-[10px] text-cyan-700 dark:text-cyanGlow-400 font-semibold">
                        {act.impactScore} Impact
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-600 dark:text-slate-400 line-clamp-2">
                      {act.description}
                    </p>
                    <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1 font-mono">
                      <span>{act.timeframe}</span>
                      <span>{act.estimatedCost}</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-xs text-slate-500 dark:text-slate-400 p-4 text-center">
                  No explicit actions queued for this role.
                </div>
              )}
            </div>

            <Link
              href="/actions"
              className="w-full inline-flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl text-xs font-semibold bg-slate-100 dark:bg-earth-900 text-cyan-700 dark:text-cyanGlow-400 border border-slate-200 dark:border-slate-700 hover:border-cyan-500 dark:hover:border-cyanGlow-500 transition-colors"
            >
              <span>View Complete Action Catalog</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
