'use client';

import React, { useState, useEffect } from 'react';
import { MapLibreMap } from '../../components/map/MapLibreMap';
import { LocationSearch } from '../../components/map/LocationSearch';
import { LOCATIONS } from '../../data/mockData';
import { fetchLocations } from '../../lib/api';
import { ClimateLocation } from '../../types';
import { useClimateStore } from '../../store/useClimateStore';
import { Compass, MapPin, Filter, ChevronRight, ChevronLeft, Layers, SlidersHorizontal, Globe } from 'lucide-react';
import Link from 'next/link';

export default function ExploreMapPage() {
  const { selectedLocation, setSelectedLocation } = useClimateStore();
  const [isDrawerOpen, setIsDrawerOpen] = useState(true);
  const [locations, setLocations] = useState<ClimateLocation[]>(LOCATIONS);

  useEffect(() => {
    let cancelled = false;
    fetchLocations().then((data) => {
      if (!cancelled) setLocations(data);
    });
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="space-y-4 w-full max-w-none">
      {/* Top Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-white/70 dark:bg-earth-900/60 p-3.5 rounded-2xl border border-slate-200 dark:border-slate-800/80 backdrop-blur-md shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-100 dark:bg-cyanGlow-500/10 border border-cyan-300 dark:border-cyanGlow-500/30 flex items-center justify-center text-cyan-600 dark:text-cyanGlow-400 shrink-0">
            <Compass className="w-5 h-5 animate-spin-slow" />
          </div>
          <div>
            <h1 className="text-xl font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <span>Explore Spatial Observation Map</span>
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-full bg-cyan-100 dark:bg-cyanGlow-500/20 text-cyan-700 dark:text-cyanGlow-400 border border-cyan-300 dark:border-cyanGlow-500/30">
                Full-Window View
              </span>
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Interactive high-resolution Earth observation canvas powered by MapLibre GL JS vector terrain &amp; multi-spectral satellite tiles.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Quick drawer toggle button */}
          <button
            onClick={() => setIsDrawerOpen(!isDrawerOpen)}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-xl bg-slate-100 dark:bg-earth-950 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:text-cyan-600 dark:hover:text-cyanGlow-400 hover:border-cyan-400 dark:hover:border-cyanGlow-500/50 transition-all shadow-sm"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>{isDrawerOpen ? 'Hide Observation Sites' : `Show Observation Sites (${locations.length})`}</span>
            {isDrawerOpen ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
          </button>

          <div className="w-72 hidden xl:block">
            <LocationSearch />
          </div>
        </div>
      </div>

      {/* Expanded Map Window Layout */}
      <div className="relative w-full rounded-2xl overflow-hidden shadow-2xl border border-slate-200 dark:border-slate-800">
        {/* Full-Window Map Component */}
        <MapLibreMap
          height="calc(100vh - 195px)"
          className="min-h-[720px]"
          showControls={true}
        />

        {/* Collapsible Floating Observation Sites Drawer */}
        {isDrawerOpen && (
          <div className="absolute top-4 right-4 bottom-16 w-80 md:w-88 glass-panel border border-slate-200 dark:border-slate-700/80 p-4 z-20 flex flex-col justify-between shadow-2xl animate-in slide-in-from-right-5 duration-300 backdrop-blur-xl">
            <div className="space-y-3 flex-1 overflow-hidden flex flex-col">
              <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-2.5">
                <div className="flex items-center gap-2">
                  <Globe className="w-4 h-4 text-cyan-600 dark:text-cyanGlow-400" />
                  <span className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
                    Observation Sites ({locations.length})
                  </span>
                </div>
                <button
                  onClick={() => setIsDrawerOpen(false)}
                  className="p-1 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  title="Close Drawer"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>

              {/* Sites List */}
              <div className="space-y-2 overflow-y-auto pr-1 flex-1">
                {locations.map((loc) => {
                  const isSelected = selectedLocation.id === loc.id;
                  return (
                    <div
                      key={loc.id}
                      onClick={() => setSelectedLocation(loc)}
                      className={`p-3 rounded-xl cursor-pointer border transition-all ${
                        isSelected
                          ? 'bg-cyan-50 dark:bg-cyanGlow-500/10 border-cyan-300 dark:border-cyanGlow-500/50 text-slate-900 dark:text-slate-100 shadow-md dark:shadow-glow-cyan'
                          : 'bg-white/80 dark:bg-earth-950/70 border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:border-cyan-300 dark:hover:border-slate-700 hover:bg-slate-50 dark:hover:bg-earth-850'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="font-semibold text-xs text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
                          <MapPin className={`w-3.5 h-3.5 shrink-0 ${isSelected ? 'text-cyan-600 dark:text-cyanGlow-400' : 'text-slate-400'}`} />
                          <span className="truncate max-w-[150px]">{loc.name}</span>
                        </div>
                        <span className={`text-[10px] px-1.5 py-0.2 rounded font-semibold border ${
                          loc.riskLevel === 'Severe' 
                            ? 'bg-rose-100 text-rose-700 border-rose-300 dark:bg-rose-500/20 dark:text-rose-400 dark:border-rose-500/30' 
                            : 'bg-amber-100 text-amber-700 border-amber-300 dark:bg-amber-500/20 dark:text-amber-400 dark:border-amber-500/30'
                        }`}>
                          {loc.riskLevel}
                        </span>
                      </div>

                      <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 line-clamp-1">
                        {loc.landform}
                      </div>

                      <div className="mt-2 pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[10px] text-slate-500 dark:text-slate-400">
                        <span>{loc.country}</span>
                        <span className="font-mono text-cyan-700 dark:text-cyanGlow-400">{loc.elevation}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Quick Focus Link */}
            <div className="pt-3 border-t border-slate-200 dark:border-slate-800 mt-2">
              <Link
                href="/location"
                className="w-full inline-flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl text-xs font-semibold bg-cyan-600 hover:bg-cyan-500 text-white dark:bg-cyanGlow-500/20 dark:hover:bg-cyanGlow-500/30 dark:text-cyanGlow-400 border border-cyan-500 dark:border-cyanGlow-500/40 transition-all shadow-sm"
              >
                <span>Analyze {selectedLocation.name}</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        )}

        {/* Quick Site Jump Dock along bottom edge */}
        <div className="absolute bottom-4 right-4 z-10 flex items-center gap-1.5 overflow-x-auto max-w-[calc(100%-350px)] hidden md:flex glass-panel p-1.5 border border-slate-200 dark:border-slate-800 shadow-xl backdrop-blur-md">
          <span className="text-[10px] font-bold text-slate-400 uppercase px-2 font-mono">Quick Jump:</span>
          {locations.map((loc) => {
            const isSelected = selectedLocation.id === loc.id;
            return (
              <button
                key={loc.id}
                onClick={() => setSelectedLocation(loc)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all whitespace-nowrap ${
                  isSelected
                    ? 'bg-cyan-500 text-white dark:bg-cyanGlow-500 dark:text-earth-950 font-bold shadow-sm'
                    : 'bg-white/80 dark:bg-earth-900 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
              >
                {loc.name.split(' ')[0]}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
