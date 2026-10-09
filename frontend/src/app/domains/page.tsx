'use client';

import React, { useState, useEffect } from 'react';
import { DomainCard } from '../../components/domains/DomainCard';
import { ENVIRONMENTAL_DOMAINS } from '../../data/mockData';
import { fetchDomains } from '../../lib/api';
import { EnvironmentalDomain } from '../../types';
import { Layers, Search, RefreshCw } from 'lucide-react';
import { EmptyState } from '../../components/common/EmptyState';

export default function EnvironmentalDomainsPage() {
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [domains, setDomains] = useState<EnvironmentalDomain[]>(ENVIRONMENTAL_DOMAINS);
  const [isLoading, setIsLoading] = useState(true);
  const [isApiConnected, setIsApiConnected] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    fetchDomains()
      .then((data) => {
        if (!cancelled) {
          setDomains(data);
          // If data came from API (not identical reference to mock), mark connected
          setIsApiConnected(data !== ENVIRONMENTAL_DOMAINS);
          setIsLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  const filtered = domains.filter((d) => {
    const matchesStatus = statusFilter === 'all' || d.status === statusFilter;
    const matchesSearch =
      d.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.primaryRisk.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Layers className="w-6 h-6 text-cyan-600 dark:text-cyanGlow-400" />
            <span>Environmental Domains Catalog</span>
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-1.5">
            Systematic classification of Earth&apos;s 9 key biomes and microclimate ecosystems.
            {isApiConnected && (
              <span className="px-1.5 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 text-[10px] font-mono border border-emerald-200 dark:border-emerald-500/20">
                ● Live API
              </span>
            )}
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Filter domains..."
              className="bg-white dark:bg-earth-900 border border-slate-300 dark:border-slate-700 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:border-cyan-500 dark:focus:border-cyanGlow-500 shadow-sm"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-white dark:bg-earth-900 border border-slate-300 dark:border-slate-700 rounded-xl px-3 py-1.5 text-xs text-slate-800 dark:text-slate-100 focus:outline-none focus:border-cyan-500 dark:focus:border-cyanGlow-500 shadow-sm"
          >
            <option value="all">All Statuses</option>
            <option value="Critical Risk">Critical Risk</option>
            <option value="Vulnerable">Vulnerable</option>
            <option value="Stable">Stable</option>
            <option value="Monitoring">Monitoring</option>
          </select>
        </div>
      </div>

      {/* Domain Cards Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 9 }).map((_, i) => (
            <div
              key={i}
              className="h-48 rounded-2xl bg-slate-100 dark:bg-earth-900 animate-pulse border border-slate-200 dark:border-slate-800"
            />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((domain) => (
            <DomainCard key={domain.id} domain={domain} />
          ))}
        </div>
      )}

      {/* Sensor Ingest Pipeline Banner */}
      <section className="mt-8">
        <EmptyState
          title="Awaiting High-Frequency Domain Multispectral Layers"
          description="Multispectral resolution algorithms (NDVI, NDWI, LST) for these 9 domains are awaiting raw satellite raster tile streaming."
          sensor="Sentinel-2 10m Multispectral STAC"
        />
      </section>
    </div>
  );
}
