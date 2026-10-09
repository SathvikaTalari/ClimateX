'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { ClimateLocation, CompositeMode } from '../../types';
import {
  useLocationSpatialFeatures,
  useProcessSceneMutation,
  useProcessedImageHistogram,
  useCompositeUrl,
  useSpatialFeatureExportUrls,
  useProcessingStatus,
} from '../../hooks/useEOProcessing';
import { useScenesByLocation } from '../../hooks/useEOSearch';
import {
  Cpu, Droplets, Trees, Building2, Activity, AlertCircle, Loader2,
  Sparkles, Layers, Lock, CheckCircle2, BarChart3, Download, Image,
  Thermometer, Eye, EyeOff, FileJson, FileText, Sigma,
} from 'lucide-react';

type IndexTab = 'NDVI' | 'NDWI' | 'NDBI' | 'LST';

interface EOProcessingPanelProps {
  location: ClimateLocation;
  selectedSceneId?: string | number;
}

export const EOProcessingPanel: React.FC<EOProcessingPanelProps> = ({
  location,
  selectedSceneId: initialSelectedSceneId,
}) => {
  const [activeTab, setActiveTab]         = useState<IndexTab>('NDVI');
  const [activeSceneId, setActiveSceneId] = useState<string | number | undefined>(initialSelectedSceneId);
  const [compositeMode, setCompositeMode] = useState<CompositeMode>('RGB');
  const [showComposite, setShowComposite] = useState(false);
  const [showHistogram, setShowHistogram] = useState(false);
  const [compositeKey, setCompositeKey]   = useState(0); // Force-reload composite

  const { data: scenes } = useScenesByLocation(location.id);

  // Default to first raster-ready scene
  useEffect(() => {
    if (initialSelectedSceneId) {
      setActiveSceneId(initialSelectedSceneId);
    } else if (scenes && scenes.length > 0) {
      const readyScene = scenes.find((s) => s.file_path);
      setActiveSceneId(readyScene ? readyScene.scene_id : scenes[0].scene_id);
    }
  }, [initialSelectedSceneId, scenes]);

  const activeSceneObj    = scenes?.find((s) => s.scene_id === activeSceneId);
  const isRasterAvailable = Boolean(activeSceneObj?.file_path);

  const { data: spatialFeatures, isLoading, refetch } = useLocationSpatialFeatures(location.id);
  const { data: processingStatus } = useProcessingStatus(activeSceneId);
  const processMutation = useProcessSceneMutation();

  // Find active feature for current tab
  const currentFeature = spatialFeatures?.find((f) => f.index_name === activeTab);
  const statusImage = processingStatus?.find((p) => p.index_name === activeTab && p.status === 'completed');

  // Histogram (resolves processed image ID from spatial feature or processing status)
  const processedImageId = currentFeature?.processed_image_id || statusImage?.id;
  const { data: histogram, isLoading: histLoading } = useProcessedImageHistogram(
    showHistogram ? processedImageId : undefined
  );

  // Composite URL (direct <img> source)
  const compositeUrl = useCompositeUrl(
    showComposite ? activeSceneId : undefined,
    compositeMode,
    location.id
  );

  // Export URLs
  const { geojsonUrl, csvUrl } = useSpatialFeatureExportUrls(location.id, activeTab);

  const handleRunProcessing = useCallback(async (indexName: IndexTab) => {
    const targetScene = activeSceneId ?? (scenes && scenes.length > 0 ? scenes[0].scene_id : null);
    if (!targetScene) return;
    try {
      await processMutation.mutateAsync({ sceneIdentifier: targetScene, req: { index_name: indexName, location_id: location.id } });
      await refetch();
    } catch (err) {
      console.error("Processing failed:", err);
    }
  }, [activeSceneId, scenes, location.id, processMutation, refetch]);

  // Auto-trigger calculation when switching locations/tabs if feature is not computed yet
  useEffect(() => {
    if (isRasterAvailable && !isLoading && !currentFeature && !processMutation.isPending && activeSceneId) {
      handleRunProcessing(activeTab);
    }
  }, [isRasterAvailable, isLoading, currentFeature, processMutation.isPending, activeSceneId, activeTab, handleRunProcessing]);

  const handleCompositeModeChange = (mode: CompositeMode) => {
    setCompositeMode(mode);
    setCompositeKey((k) => k + 1);
  };

  // ── Index metadata ─────────────────────────────────────────────────────────
  const getIndexMeta = (name: string) => {
    switch (name) {
      case 'NDVI': return { title: 'Normalized Difference Vegetation Index (NDVI)', icon: Trees,       color: 'text-emerald-500', bg: 'bg-emerald-500/10 border-emerald-500/30', desc: 'Measures vegetation health, canopy density, and agricultural vitality.' };
      case 'NDWI': return { title: 'Normalized Difference Water Index (NDWI)',      icon: Droplets,    color: 'text-blue-500',    bg: 'bg-blue-500/10 border-blue-500/30',    desc: 'Delineates open water bodies, flood extent, and vegetation water content.' };
      case 'NDBI': return { title: 'Normalized Difference Built-Up Index (NDBI)',   icon: Building2,   color: 'text-purple-500',  bg: 'bg-purple-500/10 border-purple-500/30', desc: 'Highlights urban built-up areas and impervious surface density.' };
      case 'LST':  return { title: 'Land Surface Temperature (LST °C)',             icon: Thermometer, color: 'text-orange-500',  bg: 'bg-orange-500/10 border-orange-500/30', desc: 'Calibrated surface thermal energy derived from infrared band inversion.' };
      default:     return { title: name, icon: Activity, color: 'text-cyan-500', bg: 'bg-cyan-500/10 border-cyan-500/30', desc: 'Environmental raster feature.' };
    }
  };

  const meta     = getIndexMeta(activeTab);
  const MetaIcon = meta.icon;

  // ── Histogram chart helper ─────────────────────────────────────────────────
  const renderHistogram = () => {
    if (histLoading) return (
      <div className="flex items-center justify-center gap-2 py-6 text-xs text-slate-500">
        <Loader2 className="w-4 h-4 animate-spin text-cyan-500" />
        <span>Computing pixel distribution...</span>
      </div>
    );
    if (!histogram) return (
      <div className="py-4 text-center text-xs text-slate-500 dark:text-slate-400">
        No histogram available. Process {activeTab} first.
      </div>
    );

    const maxCount = Math.max(...histogram.counts, 1);
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between text-[10px] text-slate-500 dark:text-slate-400 font-mono">
          <span>{histogram.index_name} Pixel Distribution</span>
          <span>{histogram.total_pixels.toLocaleString()} valid px · {histogram.num_bins} bins</span>
        </div>
        <div className="flex items-end gap-px h-20 w-full bg-slate-50 dark:bg-earth-950/60 rounded-lg px-1 py-1 overflow-hidden">
          {histogram.counts.map((count, i) => {
            const heightPct = (count / maxCount) * 100;
            return (
              <div
                key={i}
                title={`${histogram.bin_midpoints[i].toFixed(3)}: ${count} px`}
                className="flex-1 rounded-sm transition-all duration-300"
                style={{
                  height: `${Math.max(heightPct, 2)}%`,
                  background: `hsl(${180 + (i / histogram.num_bins) * 80}, 70%, 55%)`,
                  opacity: 0.85,
                }}
              />
            );
          })}
        </div>
        <div className="flex justify-between text-[10px] font-mono text-slate-500">
          <span>{histogram.bin_edges[0].toFixed(3)}</span>
          <span className="text-slate-400">← {activeTab} value range →</span>
          <span>{histogram.bin_edges[histogram.bin_edges.length - 1].toFixed(3)}</span>
        </div>
      </div>
    );
  };

  return (
    <div className="glass-panel p-6 border border-slate-200 dark:border-slate-800 space-y-5">

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-cyan-600 dark:text-cyanGlow-400" />
            <span>Analysis-Ready Earth Observation Features</span>
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Zonal statistics · index calculation · composite rendering for{' '}
            <span className="font-semibold text-slate-800 dark:text-slate-200">{location.name}</span>
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
          {/* Scene Selector */}
          {scenes && scenes.length > 0 && (
            <div className="flex items-center gap-1.5 bg-slate-50 dark:bg-earth-950 px-2.5 py-1 rounded-xl border border-slate-200 dark:border-slate-800 text-xs">
              <Layers className="w-3.5 h-3.5 text-cyan-600 dark:text-cyanGlow-400 flex-shrink-0" />
              <select
                value={activeSceneId || ''}
                onChange={(e) => setActiveSceneId(e.target.value)}
                className="bg-transparent text-slate-800 dark:text-slate-200 font-mono text-[11px] outline-none cursor-pointer max-w-[200px] truncate"
              >
                {scenes.map((s) => (
                  <option key={s.id} value={s.scene_id} className="dark:bg-earth-900">
                    {s.file_path ? '✓ [Raster Ready]' : '⚠ [Metadata Only]'} {s.scene_id}
                  </option>
                ))}
              </select>
            </div>
          )}

          <button
            onClick={() => handleRunProcessing(activeTab)}
            disabled={processMutation.isPending || !isRasterAvailable}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold bg-cyan-600 hover:bg-cyan-500 text-white transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {processMutation.isPending ? (
              <><Loader2 className="w-3.5 h-3.5 animate-spin" /><span>Processing...</span></>
            ) : (
              <><Sparkles className="w-3.5 h-3.5" /><span>Compute {activeTab}</span></>
            )}
          </button>
        </div>
      </div>

      {/* ── Metadata-Only Warning ───────────────────────────────────────────── */}
      {!isRasterAvailable && activeSceneObj && (
        <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-700 dark:text-amber-400 flex items-start gap-2 text-xs">
          <Lock className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <div>
            <div className="font-bold">Raster Bytes Unavailable — Metadata-Only Scene</div>
            <div>Select a <strong>✓ [Raster Ready]</strong> demo scene above to enable processing and composite rendering.</div>
          </div>
        </div>
      )}

      {/* ── Error Banner ───────────────────────────────────────────────────── */}
      {processMutation.isError && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-700 dark:text-rose-400 flex items-start gap-2 text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <div>
            <div className="font-bold">EO Raster Processing Error</div>
            <div>{processMutation.error.message}</div>
          </div>
        </div>
      )}

      {/* ── Index Tabs ─────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-1.5 flex-wrap border-b border-slate-200 dark:border-slate-800 pb-3">
        {(['NDVI', 'NDWI', 'NDBI', 'LST'] as IndexTab[]).map((tab) => {
          const m = getIndexMeta(tab);
          const Icon = m.icon;
          const isActive = activeTab === tab;
          const hasData = spatialFeatures?.some((f) => f.index_name === tab);
          return (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all relative ${
                isActive
                  ? 'bg-cyan-600 text-white shadow-sm'
                  : 'bg-slate-100 dark:bg-earth-900 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab}</span>
              {hasData && (
                <CheckCircle2 className="w-3 h-3 text-emerald-400 absolute -top-1 -right-1" />
              )}
            </button>
          );
        })}
      </div>

      {/* ── Index Info Card ─────────────────────────────────────────────────── */}
      <div className={`p-3.5 rounded-xl border ${meta.bg} space-y-1`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MetaIcon className={`w-4 h-4 ${meta.color}`} />
            <h3 className="text-xs font-bold text-slate-900 dark:text-slate-100">{meta.title}</h3>
          </div>
          <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-white/60 dark:bg-earth-900/60 text-slate-600 dark:text-slate-300">
            EPSG:4326 · PostGIS
          </span>
        </div>
        <p className="text-[11px] text-slate-600 dark:text-slate-400">{meta.desc}</p>
      </div>

      {/* ── Zonal Statistics ────────────────────────────────────────────────── */}
      {isLoading ? (
        <div className="flex items-center justify-center gap-2 py-4 text-xs text-slate-500">
          <Loader2 className="w-4 h-4 animate-spin text-cyan-500" />
          <span>Fetching spatial statistics...</span>
        </div>
      ) : currentFeature ? (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
          {[
            { label: 'Mean Value', value: currentFeature.mean_value?.toFixed(4), icon: Activity, unit: activeTab === 'LST' ? '°C' : '' },
            { label: 'Minimum',    value: currentFeature.min_value?.toFixed(4),  icon: Activity, unit: activeTab === 'LST' ? '°C' : '' },
            { label: 'Maximum',    value: currentFeature.max_value?.toFixed(4),  icon: Activity, unit: activeTab === 'LST' ? '°C' : '' },
            { label: 'Std Dev',    value: currentFeature.std_dev?.toFixed(4),    icon: Sigma,    unit: '' },
            { label: 'Valid Pixels', value: currentFeature.valid_pixels?.toLocaleString(), icon: CheckCircle2, unit: 'px', cyan: true },
          ].map(({ label, value, unit, cyan }) => (
            <div key={label} className="bg-slate-50 dark:bg-earth-950/80 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
              <div className="text-[10px] text-slate-500 dark:text-slate-400 uppercase tracking-wider">{label}</div>
              <div className={`text-sm font-bold font-mono mt-0.5 ${cyan ? 'text-cyan-600 dark:text-cyanGlow-400' : 'text-slate-900 dark:text-slate-100'}`}>
                {value ?? 'N/A'}{value && unit ? ` ${unit}` : ''}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-6 text-center space-y-2 bg-slate-50/50 dark:bg-earth-950/40 rounded-xl border border-slate-200 dark:border-slate-800">
          <AlertCircle className="w-5 h-5 text-amber-500 mx-auto" />
          <div className="text-xs font-bold text-slate-800 dark:text-slate-200">Awaiting Earth Observation Data</div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 max-w-sm mx-auto">
            No computed {activeTab} statistics for this location yet. Select a{' '}
            <strong>[Raster Ready]</strong> scene above and click &quot;Compute {activeTab}&quot;.
          </p>
        </div>
      )}

      {/* ── Feature 3: Histogram Toggle ─────────────────────────────────────── */}
      {currentFeature && processedImageId && (
        <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden">
          <button
            onClick={() => setShowHistogram((v) => !v)}
            className="w-full flex items-center justify-between px-4 py-2.5 bg-slate-50 dark:bg-earth-950/60 hover:bg-slate-100 dark:hover:bg-earth-900 transition-colors text-xs font-semibold text-slate-700 dark:text-slate-300"
          >
            <span className="flex items-center gap-2">
              <BarChart3 className="w-3.5 h-3.5 text-cyan-600 dark:text-cyanGlow-400" />
              Pixel Value Distribution Histogram
            </span>
            {showHistogram ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
          </button>
          {showHistogram && (
            <div className="p-4 bg-white dark:bg-earth-950/40">
              {renderHistogram()}
            </div>
          )}
        </div>
      )}

      {/* ── Feature 1: Composite Viewer ─────────────────────────────────────── */}
      {isRasterAvailable && (
        <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden">
          <button
            onClick={() => setShowComposite((v) => !v)}
            className="w-full flex items-center justify-between px-4 py-2.5 bg-slate-50 dark:bg-earth-950/60 hover:bg-slate-100 dark:hover:bg-earth-900 transition-colors text-xs font-semibold text-slate-700 dark:text-slate-300"
          >
            <span className="flex items-center gap-2">
              <Image className="w-3.5 h-3.5 text-purple-500" />
              Satellite Composite Viewer (RGB · False-Color · SWIR)
            </span>
            {showComposite ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
          </button>

          {showComposite && (
            <div className="p-4 space-y-3 bg-white dark:bg-earth-950/40">
              {/* Mode Selector */}
              <div className="flex items-center gap-2">
                {([
                  { mode: 'RGB'         as CompositeMode, label: 'Natural Color',       desc: 'B4-B3-B2' },
                  { mode: 'FALSE_COLOR' as CompositeMode, label: 'Vegetation Infrared', desc: 'B8-B4-B3' },
                  { mode: 'SWIR'        as CompositeMode, label: 'SWIR / Urban',        desc: 'B11-B8-B4' },
                ]).map(({ mode, label, desc }) => (
                  <button
                    key={mode}
                    onClick={() => handleCompositeModeChange(mode)}
                    className={`flex-1 px-2 py-1.5 rounded-lg text-[10px] font-semibold border transition-all ${
                      compositeMode === mode
                        ? 'bg-purple-600 text-white border-purple-600'
                        : 'bg-slate-100 dark:bg-earth-900 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-800 hover:border-purple-500'
                    }`}
                  >
                    <div>{label}</div>
                    <div className={`font-mono text-[9px] mt-0.5 ${compositeMode === mode ? 'text-purple-200' : 'text-slate-400'}`}>{desc}</div>
                  </button>
                ))}
              </div>

              {/* Composite Image */}
              <div className="relative rounded-xl overflow-hidden bg-earth-950 border border-slate-200 dark:border-slate-800 min-h-[180px] flex items-center justify-center">
                {compositeUrl ? (
                  <>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      key={`${compositeUrl}-${compositeKey}`}
                      src={compositeUrl}
                      alt={`${compositeMode} composite for ${location.name}`}
                      className="w-full h-auto object-contain max-h-[320px]"
                      style={{ imageRendering: 'pixelated' }}
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                    <div className="absolute bottom-2 left-2 px-2 py-0.5 rounded bg-black/60 text-white text-[10px] font-mono">
                      {compositeMode === 'RGB' ? 'Natural Color' : compositeMode === 'FALSE_COLOR' ? 'False Color Vegetation' : 'SWIR Composite'}
                    </div>
                    <a
                      href={compositeUrl}
                      download={`composite_${activeSceneId}_${compositeMode}.png`}
                      className="absolute top-2 right-2 px-2 py-1 rounded bg-black/60 hover:bg-black/80 text-white text-[10px] font-semibold flex items-center gap-1 transition-colors"
                    >
                      <Download className="w-3 h-3" />
                      PNG
                    </a>
                  </>
                ) : (
                  <div className="text-xs text-slate-500 dark:text-slate-400 text-center p-6">
                    <Loader2 className="w-5 h-5 animate-spin text-purple-500 mx-auto mb-2" />
                    Generating composite...
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Feature 4: Export Panel ─────────────────────────────────────────── */}
      {currentFeature && (
        <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-earth-950/40 space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-700 dark:text-slate-300">
            <Download className="w-3.5 h-3.5 text-emerald-500" />
            Export {activeTab} Spatial Features
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {geojsonUrl && (
              <a
                href={geojsonUrl}
                download={`climatex_${location.id}_${activeTab}.geojson`}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition-colors"
              >
                <FileJson className="w-3 h-3" />
                Download GeoJSON
              </a>
            )}
            {csvUrl && (
              <a
                href={csvUrl}
                download={`climatex_${location.id}_${activeTab}.csv`}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold bg-blue-600 hover:bg-blue-500 text-white transition-colors"
              >
                <FileText className="w-3 h-3" />
                Download CSV
              </a>
            )}
            <span className="text-[10px] text-slate-500 dark:text-slate-400">
              PostGIS-backed · EPSG:4326 · GIS-ready
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
