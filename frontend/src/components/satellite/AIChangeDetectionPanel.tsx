'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { ClimateLocation, MLJobOut, MLResultOut, IngestedSceneForML, ChangeCategoryOut } from '../../types';
import {
  useIngestedScenesForML,
  useSubmitChangeDetection,
  useMLJob,
} from '../../hooks/useMLChangeDetection';
import { runDemoAnalysis } from '../../lib/api';
import {
  Brain, Satellite, AlertCircle, Loader2, CheckCircle2,
  ArrowRight, BarChart3, Info, Layers, Clock, XCircle,
  Droplets, Trees, Building2, Wheat, TrendingUp, TrendingDown,
  MapPin, FileJson, Shield, Sparkles, FlaskConical, RotateCcw,
} from 'lucide-react';

// ─── Module-level constants ───────────────────────────────────────────────────

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL
  ? `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1`
  : '/api/v1';

// ─── Props ────────────────────────────────────────────────────────────────────

interface AIChangeDetectionPanelProps {
  location: ClimateLocation;
}

// ─── Category config ──────────────────────────────────────────────────────────

const CATEGORY_CONFIG: Record<string, {
  label: string; icon: React.ElementType; color: string; bg: string; border: string;
}> = {
  vegetation_loss:     { label: 'Vegetation Loss',    icon: Trees,     color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30' },
  vegetation_gain:     { label: 'Vegetation Gain',    icon: Trees,     color: 'text-green-600 dark:text-green-400',     bg: 'bg-green-500/10',   border: 'border-green-500/30' },
  water_gain:          { label: 'Water Expansion',    icon: Droplets,  color: 'text-blue-600 dark:text-blue-400',       bg: 'bg-blue-500/10',    border: 'border-blue-500/30' },
  water_loss:          { label: 'Water Contraction',  icon: Droplets,  color: 'text-cyan-600 dark:text-cyan-400',       bg: 'bg-cyan-500/10',    border: 'border-cyan-500/30' },
  urban_gain:          { label: 'Urban Expansion',    icon: Building2, color: 'text-orange-600 dark:text-orange-400',   bg: 'bg-orange-500/10',  border: 'border-orange-500/30' },
  urban_loss:          { label: 'Urban Reduction',    icon: Building2, color: 'text-amber-600 dark:text-amber-400',     bg: 'bg-amber-500/10',   border: 'border-amber-500/30' },
  agricultural_change: { label: 'Agricultural Change',icon: Wheat,     color: 'text-yellow-600 dark:text-yellow-400',   bg: 'bg-yellow-500/10',  border: 'border-yellow-500/30' },
};

function getCategoryConfig(cat: string) {
  return CATEGORY_CONFIG[cat] || {
    label: cat.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    icon: MapPin,
    color: 'text-slate-600 dark:text-slate-400',
    bg: 'bg-slate-500/10',
    border: 'border-slate-500/30',
  };
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const configs = {
    pending:   { color: 'text-amber-600 dark:text-amber-400 bg-amber-500/10 border-amber-500/30',          icon: Clock,        label: 'Pending' },
    running:   { color: 'text-cyan-600 dark:text-cyan-400 bg-cyan-500/10 border-cyan-500/30',              icon: Loader2,      label: 'Running' },
    completed: { color: 'text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/30',  icon: CheckCircle2, label: 'Completed' },
    failed:    { color: 'text-rose-600 dark:text-rose-400 bg-rose-500/10 border-rose-500/30',              icon: XCircle,      label: 'Failed' },
  };
  const cfg = configs[status as keyof typeof configs] || configs.pending;
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold border ${cfg.color}`}>
      <Icon className={`w-3 h-3 ${status === 'running' ? 'animate-spin' : ''}`} />
      {cfg.label}
    </span>
  );
}

function SQIBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = value >= 0.7 ? 'bg-emerald-500' : value >= 0.4 ? 'bg-amber-500' : 'bg-rose-500';
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 flex items-center gap-1.5">
          <Shield className="w-3.5 h-3.5" />
          Signal Quality Index
        </span>
        <span className="text-sm font-bold font-mono text-slate-800 dark:text-slate-100">{pct}%</span>
      </div>
      <div className="h-2.5 rounded-full bg-slate-200 dark:bg-earth-800 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="text-[10px] text-slate-400 dark:text-slate-500 italic">
        Measures how clearly detected changes stand out above background noise.
        Not a model accuracy score.
      </p>
    </div>
  );
}

function ChangeCategoryCard({ cat }: { cat: ChangeCategoryOut }) {
  const cfg = getCategoryConfig(cat.category);
  const Icon = cfg.icon;
  const isGain = cat.category.includes('gain');
  const TrendIcon = isGain ? TrendingUp : TrendingDown;
  return (
    <div className={`p-3 rounded-xl border ${cfg.bg} ${cfg.border} space-y-1.5`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Icon className={`w-3.5 h-3.5 ${cfg.color}`} />
          <span className={`text-[11px] font-bold ${cfg.color}`}>{cfg.label}</span>
        </div>
        <TrendIcon className={`w-3 h-3 ${cfg.color} opacity-60`} />
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-base font-bold font-mono text-slate-900 dark:text-slate-100">
          {cat.area_km2.toFixed(2)}
        </span>
        <span className="text-[10px] text-slate-500 dark:text-slate-400">km²</span>
      </div>
      <p className="text-[10px] text-slate-500 dark:text-slate-400 leading-snug">{cat.description}</p>
    </div>
  );
}

function RunningProgress() {
  const steps = [
    'Aligning raster grids (CRS, resolution, extent)',
    'Applying nodata / cloud / shadow mask',
    'Computing per-index spectral differences (NDVI, NDWI, NDBI)',
    'Classifying changed pixels by category',
    'Calculating Signal Quality Index',
  ];
  return (
    <div className="p-4 rounded-xl bg-violet-500/8 border border-violet-500/20 space-y-3">
      <div className="flex items-center gap-2 text-sm font-semibold text-violet-700 dark:text-violet-400">
        <Loader2 className="w-4 h-4 animate-spin" />
        Spectral analysis in progress…
      </div>
      <div className="space-y-1.5">
        {steps.map((step, i) => (
          <div key={i} className="flex items-center gap-2 text-[11px] text-slate-500 dark:text-slate-400">
            <div className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse flex-shrink-0" />
            {step}
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Result Panel ─────────────────────────────────────────────────────────────

interface ResultPanelProps {
  result: MLResultOut;
  locationId: string;
  onReset: () => void;
}

function ResultPanel({ result, locationId, onReset }: ResultPanelProps) {
  const [viewMode, setViewMode] = useState<'change_map' | 'before_rgb' | 'after_rgb'>('change_map');

  const previewUrl = `${API_BASE}/ml/change-maps/${result.job_id}/preview?_t=${Date.now()}`;

  // Composite URLs for actual satellite imagery
  const beforeUrl = result.before_scene_id?.startsWith('DEMO-')
    ? `${API_BASE}/eo_data/demo/${locationId}/before_rgb.png?_t=${Date.now()}`
    : `${API_BASE}/satellite-scenes/${result.before_scene_id}/composite?mode=RGB&location_id=${locationId}`;

  const afterUrl = result.after_scene_id?.startsWith('DEMO-')
    ? `${API_BASE}/eo_data/demo/${locationId}/after_rgb.png?_t=${Date.now()}`
    : `${API_BASE}/satellite-scenes/${result.after_scene_id}/composite?mode=RGB&location_id=${locationId}`;

  const currentImgUrl = viewMode === 'before_rgb' ? beforeUrl : viewMode === 'after_rgb' ? afterUrl : previewUrl;

  return (
    <div className="space-y-4">
      {/* ── Header with New Analysis button ──────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs font-semibold text-emerald-700 dark:text-emerald-400">
          <CheckCircle2 className="w-4 h-4" />
          Analysis Complete
        </div>
        <button
          id="new-change-detection-btn"
          onClick={onReset}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 dark:bg-earth-900 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-violet-500 hover:text-violet-600 dark:hover:text-violet-400 transition-colors"
        >
          <RotateCcw className="w-3 h-3" />
          New Analysis
        </button>
      </div>

      {/* ── Visual Satellite Change Map & Photo Overlay ───────────────────── */}
      {result.job_id && (
        <div className="space-y-2">
          <div className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex flex-wrap items-center justify-between gap-2">
            <span className="flex items-center gap-2">
              <Layers className="w-3.5 h-3.5 text-violet-500" />
              Satellite Image &amp; GIS Change Overlay
            </span>
            {result.change_map_bounds && (
              <span className="text-[10px] text-slate-400 font-mono bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700">
                {result.change_map_bounds[1].toFixed(2)}°N – {result.change_map_bounds[3].toFixed(2)}°N | {result.change_map_bounds[0].toFixed(2)}°E – {result.change_map_bounds[2].toFixed(2)}°E
              </span>
            )}
          </div>

          {/* Interactive Mode Tabs */}
          <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs">
            <button
              onClick={() => setViewMode('change_map')}
              className={`flex-1 py-1.5 px-2.5 rounded-lg font-semibold transition-all ${
                viewMode === 'change_map'
                  ? 'bg-violet-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              🧠 AI Change Map Overlay
            </button>
            <button
              onClick={() => setViewMode('before_rgb')}
              className={`flex-1 py-1.5 px-2.5 rounded-lg font-semibold transition-all ${
                viewMode === 'before_rgb'
                  ? 'bg-violet-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              📷 Before ({result.before_acquisition_date || 'Date 1'})
            </button>
            <button
              onClick={() => setViewMode('after_rgb')}
              className={`flex-1 py-1.5 px-2.5 rounded-lg font-semibold transition-all ${
                viewMode === 'after_rgb'
                  ? 'bg-violet-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              📷 After ({result.after_acquisition_date || 'Date 2'})
            </button>
          </div>

          <div className="relative rounded-2xl overflow-hidden bg-slate-950 border border-slate-800 p-2 group">
            <div className="relative w-full aspect-video max-h-80 rounded-xl overflow-hidden bg-earth-950 flex items-center justify-center">
              <img
                src={currentImgUrl}
                alt="Satellite View"
                className="w-full h-full object-contain filter drop-shadow-md transition-transform duration-300 group-hover:scale-105"
                onError={(e) => {
                  if (viewMode !== 'change_map') {
                    (e.target as HTMLImageElement).src = previewUrl;
                  }
                }}
              />
              {/* GIS coordinate overlays */}
              {result.change_map_bounds && (
                <>
                  <div className="absolute top-2 left-2 px-1.5 py-0.5 rounded bg-black/60 backdrop-blur-sm text-[9px] font-mono text-slate-300 pointer-events-none">
                    {result.change_map_bounds[3].toFixed(4)}°N, {result.change_map_bounds[0].toFixed(4)}°E
                  </div>
                  <div className="absolute top-2 right-12 px-1.5 py-0.5 rounded bg-black/60 backdrop-blur-sm text-[9px] font-mono text-slate-300 pointer-events-none">
                    {result.change_map_bounds[3].toFixed(4)}°N, {result.change_map_bounds[2].toFixed(4)}°E
                  </div>
                  <div className="absolute bottom-2 left-2 px-1.5 py-0.5 rounded bg-black/60 backdrop-blur-sm text-[9px] font-mono text-slate-300 pointer-events-none">
                    {result.change_map_bounds[1].toFixed(4)}°N, {result.change_map_bounds[0].toFixed(4)}°E
                  </div>
                  <div className="absolute bottom-2 right-2 px-1.5 py-0.5 rounded bg-black/60 backdrop-blur-sm text-[9px] font-mono text-slate-300 pointer-events-none">
                    {result.change_map_bounds[1].toFixed(4)}°N, {result.change_map_bounds[2].toFixed(4)}°E
                  </div>

                  {/* North Arrow */}
                  <div className="absolute top-2 right-2 w-8 h-8 rounded-full bg-black/60 backdrop-blur-sm border border-slate-700/50 flex flex-col items-center justify-center pointer-events-none shadow-xl">
                    <div className="text-[8px] font-bold text-white mb-[1px]">N</div>
                    <svg width="8" height="10" viewBox="0 0 10 12" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M5 0L10 12L5 9.5L0 12L5 0Z" fill="#F44336"/>
                      <path d="M5 0V9.5L0 12L5 0Z" fill="#E0E0E0"/>
                    </svg>
                  </div>

                  {/* Scale Bar */}
                  <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex flex-col items-center pointer-events-none opacity-80">
                    <div className="flex items-end h-1.5 w-24 border-x border-b border-white">
                      <div className="w-1/2 h-full bg-white" />
                      <div className="w-1/2 h-full bg-black" />
                    </div>
                    <div className="text-[9px] font-semibold text-white drop-shadow-md mt-0.5">
                      2 km (approx)
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Map Legend Overlay */}
            {viewMode === 'change_map' ? (
              <div className="mt-2.5 px-3 py-2 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-wrap items-center justify-around gap-2 text-[11px]">
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#2196F3] shadow-sm shadow-blue-500/50" />
                  <span className="text-slate-300 font-medium">Water Body Change</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#4CAF50] shadow-sm shadow-green-500/50" />
                  <span className="text-slate-300 font-medium">Vegetation / Forest Change</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#FF5722] shadow-sm shadow-orange-500/50" />
                  <span className="text-slate-300 font-medium">Built-Up / Urban Change</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-slate-700" />
                  <span className="text-slate-400">Satellite Base Terrain</span>
                </div>
              </div>
            ) : (
              <div className="mt-2.5 px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800 text-center text-[11px] text-slate-300">
                🛰️ {viewMode === 'before_rgb' ? 'Before Acquisition' : 'After Acquisition'} True-Color Satellite RGB (Copernicus Sentinel-2 / USGS Landsat-8)
              </div>
            )}
          </div>
        </div>
      )}

      {/* Source scene info */}
      <div className="grid grid-cols-2 gap-2">
        {[
          { label: 'Before Scene', date: result.before_acquisition_date, id: result.before_scene_id },
          { label: 'After Scene',  date: result.after_acquisition_date,  id: result.after_scene_id },
        ].map(({ label, date, id }) => (
          <div key={label} className="p-3 rounded-xl bg-slate-50 dark:bg-earth-950/80 border border-slate-200 dark:border-slate-800">
            <div className="text-[10px] text-slate-500 dark:text-slate-400 uppercase tracking-wider">{label}</div>
            <div className="text-xs font-bold font-mono text-slate-900 dark:text-slate-100 mt-0.5">{date || '—'}</div>
            {id && <div className="text-[10px] text-slate-400 font-mono truncate mt-0.5" title={id}>{id}</div>}
          </div>
        ))}
      </div>

      {/* Summary statistics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {[
          { label: 'Area Changed',   value: result.changed_area_km2 != null ? `${result.changed_area_km2.toFixed(2)} km²` : '—', accent: false },
          { label: '% Changed',      value: result.changed_pct != null ? `${result.changed_pct.toFixed(2)}%` : '—', accent: true },
          { label: 'Valid Coverage', value: result.valid_pixel_fraction != null ? `${(result.valid_pixel_fraction * 100).toFixed(1)}%` : '—', accent: false },
          { label: 'Total Area',     value: result.total_area_km2 != null ? `${result.total_area_km2.toFixed(2)} km²` : '—', accent: false },
        ].map(({ label, value, accent }) => (
          <div key={label} className="p-3 rounded-xl bg-slate-50 dark:bg-earth-950/80 border border-slate-200 dark:border-slate-800">
            <div className="text-[10px] text-slate-500 dark:text-slate-400 uppercase tracking-wider">{label}</div>
            <div className={`text-sm font-bold font-mono mt-0.5 ${accent ? 'text-violet-600 dark:text-violet-400' : 'text-slate-900 dark:text-slate-100'}`}>
              {value}
            </div>
          </div>
        ))}
      </div>

      {/* SQI */}
      {result.signal_quality_index != null && (
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-earth-950/80 border border-slate-200 dark:border-slate-800">
          <SQIBar value={result.signal_quality_index} />
        </div>
      )}

      {/* Change categories */}
      {result.change_categories.length > 0 ? (
        <div className="space-y-2">
          <div className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-2">
            <BarChart3 className="w-3.5 h-3.5 text-violet-500" />
            Detected Change Categories
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {result.change_categories.map(cat => (
              <ChangeCategoryCard key={cat.category} cat={cat} />
            ))}
          </div>
        </div>
      ) : (
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-earth-950/60 border border-slate-200 dark:border-slate-800 text-center space-y-1">
          <CheckCircle2 className="w-4 h-4 text-emerald-500 mx-auto" />
          <div className="text-xs font-semibold text-slate-800 dark:text-slate-200">No Significant Changes Detected</div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400">
            No pixels exceeded the spectral threshold. The two scenes appear stable.
          </p>
        </div>
      )}

      {/* Algorithm provenance */}
      <div className="p-3 rounded-xl bg-slate-50 dark:bg-earth-950/60 border border-slate-200 dark:border-slate-700 space-y-1.5">
        <div className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <Info className="w-3 h-3" />
          Algorithm Provenance
        </div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-[10px] font-mono">
          <span className="text-slate-400">Algorithm</span>
          <span className="text-slate-700 dark:text-slate-300">{result.algorithm.name} v{result.algorithm.version}</span>
          <span className="text-slate-400">Type</span>
          <span className="text-slate-700 dark:text-slate-300">Threshold-based spectral analysis</span>
          <span className="text-slate-400">Indices</span>
          <span className="text-slate-700 dark:text-slate-300">{result.algorithm.indices_used.join(', ')}</span>
          <span className="text-slate-400">Evaluation</span>
          <span className="text-slate-500 dark:text-slate-500 italic">
            {result.evaluation_metrics
              ? `F1 ${(result.evaluation_metrics.f1_score ?? 0).toFixed(3)} · IoU ${(result.evaluation_metrics.iou ?? 0).toFixed(3)}`
              : 'No ground truth supplied'}
          </span>
        </div>
        <p className="text-[10px] text-slate-400 italic">Unsupervised · No trained model weights</p>
      </div>

      {/* Download */}
      {result.job_id && (
        <a
          href={`${API_BASE}/ml/change-maps/${result.job_id}/file`}
          download={`change_map_${result.job_id}.tif`}
          className="inline-flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold bg-slate-100 dark:bg-earth-900 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-violet-500 transition-colors"
        >
          <FileJson className="w-3.5 h-3.5 text-violet-500" />
          Download Change Map (GeoTIFF · uint8 · LZW)
        </a>
      )}
    </div>
  );
}

// ─── Main Panel ───────────────────────────────────────────────────────────────

export const AIChangeDetectionPanel: React.FC<AIChangeDetectionPanelProps> = ({ location }) => {
  const { data: scenes, isLoading: scenesLoading } = useIngestedScenesForML(location.id);
  const submitMutation = useSubmitChangeDetection();

  const [beforeDbId, setBeforeDbId] = useState<number | null>(null);
  const [afterDbId, setAfterDbId]   = useState<number | null>(null);
  const [activeJobId, setActiveJobId]   = useState<string | null>(null);
  const [lastResult, setLastResult]     = useState<MLResultOut | null>(null);
  const [demoLoading, setDemoLoading]   = useState(false);
  const [demoError, setDemoError]       = useState<string | null>(null);

  const { data: jobData } = useMLJob(activeJobId ?? undefined);

  const hasScenes = (scenes?.length ?? 0) >= 2;

  // Auto-select first + last scene
  useEffect(() => {
    if (scenes && scenes.length >= 2 && !beforeDbId && !afterDbId) {
      setBeforeDbId(scenes[0].db_id);
      setAfterDbId(scenes[scenes.length - 1].db_id);
    }
  }, [scenes]);

  // Capture result when job completes
  useEffect(() => {
    if (jobData?.status === 'completed' && jobData.result) {
      setLastResult(jobData.result);
    }
  }, [jobData]);

  // Reset all state for a new analysis
  const handleReset = useCallback(() => {
    setActiveJobId(null);
    setLastResult(null);
    setDemoError(null);
    submitMutation.reset();
  }, [submitMutation]);

  const handleSubmit = useCallback(async () => {
    if (!beforeDbId || !afterDbId) return;
    try {
      const resp = await submitMutation.mutateAsync({
        location_id: location.id,
        before_scene_db_id: beforeDbId,
        after_scene_db_id: afterDbId,
      });
      setActiveJobId(resp.job_id);
      setLastResult(null);
    } catch (err: any) {
      console.error('Submission failed:', err);
    }
  }, [beforeDbId, afterDbId, location.id, submitMutation]);

  const handleDemo = useCallback(async () => {
    setDemoLoading(true);
    setDemoError(null);
    setLastResult(null);
    setActiveJobId(null);
    try {
      const resp = await runDemoAnalysis(location.id);
      setActiveJobId(resp.job_id);
    } catch (err: any) {
      setDemoError(err?.message || 'Failed to start demo. Is the ML service running?');
    } finally {
      setDemoLoading(false);
    }
  }, [location.id]);

  const isRunning = jobData?.status === 'pending' || jobData?.status === 'running';
  const isFailed  = jobData?.status === 'failed';
  const canRun    = !!beforeDbId && !!afterDbId && beforeDbId !== afterDbId && !isRunning;

  return (
    <div className="glass-panel p-6 border border-slate-200 dark:border-slate-800 space-y-5">

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Brain className="w-5 h-5 text-violet-600 dark:text-violet-400" />
            AI Change Detection
            <span className="text-[10px] font-mono font-normal text-slate-400 ml-1">MISCD v1.0.0</span>
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Spectral analysis · Threshold-based · Unsupervised ·{' '}
            <span className="font-semibold text-slate-700 dark:text-slate-300">{location.name}</span>
          </p>
        </div>
        {activeJobId && jobData && <StatusBadge status={jobData.status} />}
      </div>

      {/* ── EMPTY STATE: No real scenes — show Demo CTA prominently ───── */}
      {!scenesLoading && !hasScenes && !lastResult && !activeJobId && (
        <div className="space-y-4">
          {/* Demo CTA — main action */}
          <div className="p-5 rounded-2xl bg-gradient-to-br from-violet-500/10 to-indigo-500/10 border border-violet-500/30 space-y-3 text-center">
            <div className="flex items-center justify-center gap-2 text-violet-600 dark:text-violet-400">
              <Sparkles className="w-5 h-5" />
              <span className="font-bold text-sm">Try Demo Analysis</span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 max-w-xs mx-auto">
              No satellite data? No problem. Click below to generate synthetic before/after scenes
              with realistic spectral indices and run the full change-detection pipeline instantly.
            </p>
            <div className="text-[11px] text-slate-500 dark:text-slate-400 space-y-0.5">
              <div>🌿 Simulates vegetation loss &amp; recovery</div>
              <div>💧 Simulates water body expansion</div>
              <div>🏗️ Simulates urban / built-up expansion</div>
            </div>
            <button
              id="demo-change-detection-btn"
              onClick={handleDemo}
              disabled={demoLoading}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold bg-violet-600 hover:bg-violet-500 text-white transition-all shadow-lg shadow-violet-500/25 disabled:opacity-60 disabled:cursor-not-allowed mx-auto"
            >
              {demoLoading
                ? <><Loader2 className="w-4 h-4 animate-spin" />Generating demo…</>
                : <><FlaskConical className="w-4 h-4" />Run Demo Analysis</>
              }
            </button>
          </div>

          {/* Separator */}
          <div className="flex items-center gap-3">
            <div className="flex-1 border-t border-slate-200 dark:border-slate-800" />
            <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">or use real scenes</span>
            <div className="flex-1 border-t border-slate-200 dark:border-slate-800" />
          </div>

          {/* Instructions for real scenes */}
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-earth-950/60 border border-slate-200 dark:border-slate-800 space-y-2">
            <div className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
              To use real satellite data:
            </div>
            <ol className="space-y-1.5 text-xs text-slate-600 dark:text-slate-400">
              <li className="flex gap-2">
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-violet-500/20 text-violet-600 dark:text-violet-400 text-[10px] font-bold flex items-center justify-center">1</span>
                Use <strong className="text-slate-800 dark:text-slate-200">Satellite Search</strong> panel above — ingest ≥2 scenes for different dates.
              </li>
              <li className="flex gap-2">
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-violet-500/20 text-violet-600 dark:text-violet-400 text-[10px] font-bold flex items-center justify-center">2</span>
                In <strong className="text-slate-800 dark:text-slate-200">EO Features</strong> panel — compute NDVI / NDWI / NDBI for both scenes.
              </li>
              <li className="flex gap-2">
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-violet-500/20 text-violet-600 dark:text-violet-400 text-[10px] font-bold flex items-center justify-center">3</span>
                Return here — select before/after dates and click <strong className="text-slate-800 dark:text-slate-200">Run Detection</strong>.
              </li>
            </ol>
          </div>
        </div>
      )}

      {/* ── REAL SCENES available ───────────────────────────────────────── */}
      {(scenesLoading || hasScenes) && !lastResult && !activeJobId && (
        <div className="space-y-4">
          {/* Demo shortcut */}
          <div className="flex items-center justify-between p-3 rounded-xl bg-violet-500/8 border border-violet-500/20">
            <span className="text-xs text-violet-700 dark:text-violet-400">Want a quick preview?</span>
            <button
              onClick={handleDemo}
              disabled={demoLoading || isRunning}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-violet-600 hover:bg-violet-500 text-white transition-all disabled:opacity-50"
            >
              {demoLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <FlaskConical className="w-3 h-3" />}
              Try Demo
            </button>
          </div>

          <div className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-2">
            <Layers className="w-3.5 h-3.5 text-violet-500" />
            Select Before / After Scenes
          </div>

          {scenesLoading ? (
            <div className="flex items-center gap-2 text-xs text-slate-400 py-2">
              <Loader2 className="w-3.5 h-3.5 animate-spin" /> Loading scenes…
            </div>
          ) : (
            <div className="flex flex-col sm:flex-row items-end gap-3">
              {/* Before */}
              <div className="flex-1 min-w-0">
                <label className="block text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1">Before (Earlier)</label>
                <select
                  value={beforeDbId ?? ''}
                  onChange={e => setBeforeDbId(Number(e.target.value))}
                  className="w-full bg-slate-50 dark:bg-earth-950 text-slate-800 dark:text-slate-200 text-xs border border-slate-200 dark:border-slate-700 rounded-lg px-2.5 py-2 outline-none focus:ring-2 focus:ring-violet-500/40"
                >
                  <option value="">— Select scene —</option>
                  {(scenes ?? []).filter(s => s.db_id !== afterDbId).map(s => (
                    <option key={s.db_id} value={s.db_id}>
                      {s.acquisition_date} · {s.satellite || s.sensor} [{s.available_indices.join(', ')}]
                    </option>
                  ))}
                </select>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400 flex-shrink-0 mb-2.5 hidden sm:block" />
              {/* After */}
              <div className="flex-1 min-w-0">
                <label className="block text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1">After (Later)</label>
                <select
                  value={afterDbId ?? ''}
                  onChange={e => setAfterDbId(Number(e.target.value))}
                  className="w-full bg-slate-50 dark:bg-earth-950 text-slate-800 dark:text-slate-200 text-xs border border-slate-200 dark:border-slate-700 rounded-lg px-2.5 py-2 outline-none focus:ring-2 focus:ring-violet-500/40"
                >
                  <option value="">— Select scene —</option>
                  {(scenes ?? []).filter(s => s.db_id !== beforeDbId).map(s => (
                    <option key={s.db_id} value={s.db_id}>
                      {s.acquisition_date} · {s.satellite || s.sensor} [{s.available_indices.join(', ')}]
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          <button
            id="run-change-detection-btn"
            onClick={handleSubmit}
            disabled={!canRun || submitMutation.isPending}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold bg-violet-600 hover:bg-violet-500 text-white shadow-md shadow-violet-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {(isRunning || submitMutation.isPending)
              ? <><Loader2 className="w-3.5 h-3.5 animate-spin" />Analysing…</>
              : <><Satellite className="w-3.5 h-3.5" />Run AI Change Detection</>
            }
          </button>
        </div>
      )}

      {/* ── Errors ─────────────────────────────────────────────────────── */}
      {(submitMutation.isError || isFailed || demoError) && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-700 dark:text-rose-400 flex items-start gap-2 text-xs">
          <XCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <div>
            <div className="font-bold">Analysis Failed</div>
            <div className="mt-0.5">
              {demoError || submitMutation.error?.message || jobData?.error_message ||
               'An error occurred. Ensure the ML service is running on port 8001.'}
            </div>
            <button
              onClick={handleReset}
              className="mt-2 text-[11px] underline underline-offset-2 hover:no-underline"
            >
              Try again
            </button>
          </div>
        </div>
      )}

      {/* ── Running ─────────────────────────────────────────────────────── */}
      {isRunning && <RunningProgress />}

      {/* ── Results ─────────────────────────────────────────────────────── */}
      {lastResult && (
        <ResultPanel
          result={lastResult}
          locationId={location.id}
          onReset={handleReset}
        />
      )}
    </div>
  );
};
