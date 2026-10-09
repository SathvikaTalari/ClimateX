'use client';

import React from 'react';
import { MapLibreMap } from '../components/map/MapLibreMap';
import { RoleContextBanner } from '../components/roles/RoleContextBanner';
import { DomainCard } from '../components/domains/DomainCard';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorBanner } from '../components/common/ErrorBanner';
import { ROLE_INFO } from '../data/mockData';
import { useClimateStore } from '../store/useClimateStore';
import { useDomains } from '../hooks';
import { Layers, MapPin, Activity, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  const { activeRole, selectedLocation, activeDomainFilter, setActiveDomainFilter } = useClimateStore();
  const roleInfo = ROLE_INFO[activeRole];
  const { data: domains = [], isLoading, isError, refetch } = useDomains();

  const filteredDomains = activeDomainFilter === 'all'
    ? domains
    : domains.filter((d) => d.id === activeDomainFilter);

  return (
    <div className="space-y-8 max-w-[1600px] mx-auto w-full">
      {/* Role Context Notice Banner */}
      <RoleContextBanner />

      {/* Hero Section: Large Map + Quick Location Summary */}
      <section className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
                Earth Observation Dashboard
              </h1>
              <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400 border border-emerald-300 dark:border-emerald-500/30">
                Live Sensor Network
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              {roleInfo.dashboardSubhead}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href="/location"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-cyan-600 to-cyan-500 text-white dark:from-cyanGlow-600 dark:to-cyanGlow-500 dark:text-earth-950 shadow-md dark:shadow-glow-cyan hover:opacity-90 transition-opacity"
            >
              <MapPin className="w-3.5 h-3.5" />
              <span>Location Intelligence</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* Large Interactive World Map with Expanded Boundary */}
        <MapLibreMap height="600px" showControls={true} />
      </section>

      {/* Environmental Domains Grid */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <Layers className="w-5 h-5 text-cyan-600 dark:text-cyanGlow-400" />
              <span>Environmental Domains</span>
              <span className="text-xs font-mono text-slate-500 dark:text-slate-400 font-normal">
                ({domains.length || 9} Biomes Monitored)
              </span>
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Select a domain card to filter spatial observation models and target risk zones.
            </p>
          </div>

          {activeDomainFilter !== 'all' && (
            <button
              onClick={() => setActiveDomainFilter('all')}
              className="text-xs text-cyan-600 dark:text-cyanGlow-400 hover:underline font-medium"
            >
              Reset Domain Filter
            </button>
          )}
        </div>

        {isLoading ? (
          <LoadingSkeleton count={9} type="card" />
        ) : isError ? (
          <ErrorBanner message="Unable to connect to environmental domains API." onRetry={() => refetch()} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredDomains.map((domain) => (
              <DomainCard key={domain.id} domain={domain} />
            ))}
          </div>
        )}
      </section>

      {/* Sensor Ingest Status & Empty State Realism Banner */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-600 dark:text-emeraldGlow-400" />
            <span>Satellite Observation Ingest Channel</span>
          </h3>
          <span className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">Telemetry Standard: NetCDF4 / GeoTIFF</span>
        </div>

        <EmptyState
          title="Awaiting Earth Observation Telemetry Feed"
          description="High-resolution hyperspectral imagery from Sentinel-2C and Landsat-9 is currently queuing for ingestion. Downlink scheduled for next orbital pass."
          sensor="ESA Copernicus Hub / USGS Landsat STAC API"
          actionText="Refresh Sensor Connection"
          onRetry={() => alert('Sensor connection active. Awaiting satellite pass...')}
        />
      </section>
    </div>
  );
}
