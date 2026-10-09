'use client';

import React, { useState, useEffect } from 'react';
import { ClimateLocation, EOScene, SceneSearchParams } from '../../types';
import { useEOSearchMutation, useIngestSceneMutation } from '../../hooks/useEOSearch';
import { SceneCard } from './SceneCard';
import {
  Satellite,
  Search,
  Calendar,
  Cloud,
  Filter,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Info,
  RefreshCw,
} from 'lucide-react';

interface SatelliteSearchPanelProps {
  location: ClimateLocation;
  onFootprintSelect?: (scene: EOScene) => void;
}

export const SatelliteSearchPanel: React.FC<SatelliteSearchPanelProps> = ({
  location,
  onFootprintSelect,
}) => {
  // Default date range: last 30 days
  const today = new Date();
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(today.getDate() - 30);

  const [dateFrom, setDateFrom] = useState<string>(thirtyDaysAgo.toISOString().split('T')[0]);
  const [dateTo, setDateTo] = useState<string>(today.toISOString().split('T')[0]);
  const [satellite, setSatellite] = useState<string>('Sentinel-2');
  const [cloudCoverMax, setCloudCoverMax] = useState<number>(30);
  const [selectedProvider, setSelectedProvider] = useState<string>('all');

  // Search & Ingestion mutations
  const searchMutation = useEOSearchMutation();
  const ingestMutation = useIngestSceneMutation();

  const handleSearch = () => {
    const params: SceneSearchParams = {
      date_from: dateFrom,
      date_to: dateTo,
      lat: location.coordinates[0],
      lon: location.coordinates[1],
      satellite: satellite === 'all' ? undefined : satellite,
      cloud_cover_max: cloudCoverMax,
      providers: selectedProvider === 'all' ? undefined : [selectedProvider],
      limit: 15,
    };
    searchMutation.mutate(params);
  };

  // Trigger initial search when location changes
  useEffect(() => {
    handleSearch();
  }, [location.id]);

  const handleIngestScene = async (scene: EOScene, downloadRaster: boolean) => {
    await ingestMutation.mutateAsync({
      scene_id: scene.scene_id,
      provider: scene.provider,
      satellite: scene.satellite,
      sensor: scene.sensor,
      acquisition_date: scene.acquisition_date,
      cloud_cover: scene.cloud_cover ?? undefined,
      resolution_m: scene.resolution_m ?? undefined,
      bbox: scene.bbox,
      footprint_geojson: scene.footprint_geojson,
      source_url: scene.source_url ?? undefined,
      bands: scene.bands,
      metadata: scene.metadata,
      location_id: location.id,
      download_raster: downloadRaster,
    });
  };

  return (
    <div className="glass-panel p-6 border border-slate-200 dark:border-slate-800 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Satellite className="w-5 h-5 text-cyan-600 dark:text-cyanGlow-400" />
            <span>Earth Observation Satellite Catalog</span>
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Query real Copernicus Sentinel & USGS Landsat satellite passes for{' '}
            <span className="font-semibold text-slate-800 dark:text-slate-200">{location.name}</span>
          </p>
        </div>

        <button
          onClick={handleSearch}
          disabled={searchMutation.isPending}
          className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-cyan-600 hover:bg-cyan-500 text-white transition-all shadow-md dark:shadow-cyan-900/30 disabled:opacity-50"
        >
          {searchMutation.isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Querying Providers...</span>
            </>
          ) : (
            <>
              <Search className="w-4 h-4" />
              <span>Search Available Scenes</span>
            </>
          )}
        </button>
      </div>

      {/* Filter Controls Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 p-4 bg-slate-50 dark:bg-earth-950/60 rounded-xl border border-slate-200 dark:border-slate-800">
        {/* Date From */}
        <div className="space-y-1.5">
          <label className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-cyan-600 dark:text-cyanGlow-400" />
            <span>Date From</span>
          </label>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="w-full text-xs p-2 rounded-lg bg-white dark:bg-earth-900 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-cyan-500 outline-none"
          />
        </div>

        {/* Date To */}
        <div className="space-y-1.5">
          <label className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-cyan-600 dark:text-cyanGlow-400" />
            <span>Date To</span>
          </label>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="w-full text-xs p-2 rounded-lg bg-white dark:bg-earth-900 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-cyan-500 outline-none"
          />
        </div>

        {/* Satellite Selection */}
        <div className="space-y-1.5">
          <label className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
            <Satellite className="w-3.5 h-3.5 text-cyan-600 dark:text-cyanGlow-400" />
            <span>Satellite / Sensor</span>
          </label>
          <select
            value={satellite}
            onChange={(e) => setSatellite(e.target.value)}
            className="w-full text-xs p-2 rounded-lg bg-white dark:bg-earth-900 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-cyan-500 outline-none"
          >
            <option value="all">All Satellites</option>
            <option value="Sentinel-2">Sentinel-2 (Optical 10m MSI)</option>
            <option value="Sentinel-1">Sentinel-1 (Radar SAR C-band)</option>
            <option value="Landsat-8">Landsat-8 (USGS OLI-TIRS 30m)</option>
            <option value="Landsat-9">Landsat-9 (USGS OLI-2 30m)</option>
          </select>
        </div>

        {/* Max Cloud Cover */}
        <div className="space-y-1.5">
          <div className="flex justify-between items-center text-[11px] font-semibold text-slate-700 dark:text-slate-300">
            <span className="flex items-center gap-1.5">
              <Cloud className="w-3.5 h-3.5 text-amber-500" />
              <span>Max Cloud Cover</span>
            </span>
            <span className="font-mono text-cyan-600 dark:text-cyanGlow-400">{cloudCoverMax}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            step="5"
            value={cloudCoverMax}
            onChange={(e) => setCloudCoverMax(Number(e.target.value))}
            className="w-full accent-cyan-500 cursor-pointer"
          />
        </div>
      </div>

      {/* Results Section */}
      <div className="space-y-4">
        {/* Loading State */}
        {searchMutation.isPending && (
          <div className="p-8 text-center space-y-3 bg-slate-50/50 dark:bg-earth-950/40 rounded-xl border border-slate-200 dark:border-slate-800">
            <Loader2 className="w-8 h-8 animate-spin text-cyan-600 dark:text-cyanGlow-400 mx-auto" />
            <div className="text-sm font-semibold text-slate-800 dark:text-slate-200">
              Searching Copernicus STAC & USGS Catalogs...
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Querying live satellite orbit geometry and cloud cover for coordinates [{location.coordinates[0]}° N, {location.coordinates[1]}° W].
            </p>
          </div>
        )}

        {/* Error State */}
        {searchMutation.isError && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-700 dark:text-rose-400 flex items-start gap-3 text-xs">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-bold">EO Provider Search Error</div>
              <div>{searchMutation.error.message}</div>
              <button
                onClick={handleSearch}
                className="mt-2 underline font-semibold hover:text-rose-900 dark:hover:text-rose-200"
              >
                Retry Query
              </button>
            </div>
          </div>
        )}

        {/* Success / Results Display */}
        {searchMutation.isSuccess && (
          <>
            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 font-mono px-1">
              <span>
                Found <strong className="text-slate-800 dark:text-slate-200">{searchMutation.data.length}</strong> available satellite scenes
              </span>
              <span>Coordinates: [{location.coordinates[0]}° N, {location.coordinates[1]}° W]</span>
            </div>

            {searchMutation.data.length === 0 ? (
              <div className="p-8 text-center space-y-2 bg-slate-50/50 dark:bg-earth-950/40 rounded-xl border border-slate-200 dark:border-slate-800">
                <Info className="w-6 h-6 text-amber-500 mx-auto" />
                <div className="text-sm font-bold text-slate-800 dark:text-slate-200">
                  No Satellite Scenes Found
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto">
                  Try widening the date range or increasing the maximum cloud cover percentage filter.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {searchMutation.data.map((scene) => (
                  <SceneCard
                    key={`${scene.provider}-${scene.scene_id}`}
                    scene={scene}
                    locationId={location.id}
                    onIngest={handleIngestScene}
                    onSelectFootprint={onFootprintSelect}
                    isIngesting={ingestMutation.isPending}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};
