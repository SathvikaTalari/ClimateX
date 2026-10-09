'use client';

import React, { useState } from 'react';
import { EOScene } from '../../types';
import { IngestionStatusBadge } from './IngestionStatusBadge';
import {
  Satellite,
  Cloud,
  Calendar,
  Layers,
  Download,
  CheckCircle,
  Eye,
  Lock,
  ExternalLink,
} from 'lucide-react';

interface SceneCardProps {
  scene: EOScene;
  locationId?: string;
  onIngest: (scene: EOScene, downloadRaster: boolean) => Promise<void>;
  onSelectFootprint?: (scene: EOScene) => void;
  isIngesting?: boolean;
}

export const SceneCard: React.FC<SceneCardProps> = ({
  scene,
  locationId,
  onIngest,
  onSelectFootprint,
  isIngesting = false,
}) => {
  const [ingestMode, setIngestMode] = useState<'full' | 'meta'>('full');
  const [ingestedStatus, setIngestedStatus] = useState<string | null>(
    scene.is_already_ingested ? 'completed' : null
  );

  const handleIngestClick = async (downloadRaster: boolean) => {
    try {
      setIngestedStatus('processing');
      await onIngest(scene, downloadRaster);
      setIngestedStatus('completed');
    } catch (error) {
      setIngestedStatus('failed');
    }
  };

  const getProviderBadge = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'copernicus':
        return 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30';
      case 'usgs':
        return 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30';
      case 'up42':
        return 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/30';
      default:
        return 'bg-slate-500/10 text-slate-600 dark:text-slate-400 border-slate-500/30';
    }
  };

  return (
    <div className="bg-slate-50/80 dark:bg-earth-950/80 p-4 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-cyan-500/50 transition-all space-y-3 shadow-sm">
      {/* Top Header Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${getProviderBadge(scene.provider)}`}>
            {scene.provider}
          </span>
          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-cyan-100 dark:bg-cyanGlow-500/20 text-cyan-700 dark:text-cyanGlow-400 border border-cyan-300 dark:border-cyanGlow-500/30">
            {scene.satellite}
          </span>
          {scene.processing_level && (
            <span className="px-2 py-0.5 rounded text-[10px] font-mono text-slate-500 bg-slate-200/60 dark:bg-slate-800">
              {scene.processing_level}
            </span>
          )}
        </div>

        {/* Status Badge */}
        {ingestedStatus && <IngestionStatusBadge status={ingestedStatus} />}
      </div>

      {/* Scene ID & Preview Thumbnail */}
      <div className="flex gap-3 items-start">
        {scene.thumbnail_url && (
          <img
            src={scene.thumbnail_url}
            alt={scene.scene_id}
            className="w-14 h-14 object-cover rounded-lg border border-slate-200 dark:border-slate-800 flex-shrink-0 shadow-sm bg-slate-200 dark:bg-earth-900"
            onError={(e) => { (e.target as HTMLElement).style.display = 'none'; }}
          />
        )}
        <div className="flex-1 min-w-0">
          <div className="text-xs font-mono font-bold text-slate-900 dark:text-slate-100 truncate" title={scene.scene_id}>
            {scene.scene_id}
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400">
            Sensor: <span className="font-semibold">{scene.sensor}</span>
          </div>
        </div>
      </div>

      {/* Attributes Grid */}
      <div className="grid grid-cols-3 gap-2 text-[11px] pt-1 border-t border-slate-200/80 dark:border-slate-800/80">
        <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
          <Calendar className="w-3.5 h-3.5 text-cyan-600 dark:text-cyanGlow-400" />
          <span className="font-mono">{scene.acquisition_date}</span>
        </div>

        <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
          <Cloud className="w-3.5 h-3.5 text-amber-500" />
          <span className="font-mono">
            {scene.cloud_cover !== undefined && scene.cloud_cover !== null
              ? `${scene.cloud_cover.toFixed(1)}%`
              : 'N/A'}
          </span>
        </div>

        <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
          <Layers className="w-3.5 h-3.5 text-emerald-500" />
          <span className="font-mono">
            {scene.resolution_m ? `${scene.resolution_m}m GSD` : 'Standard'}
          </span>
        </div>
      </div>

      {/* Bands & Credential Note */}
      {scene.bands && scene.bands.length > 0 && (
        <div className="flex items-center gap-1 text-[10px] text-slate-500 dark:text-slate-400 overflow-x-auto py-0.5">
          <span className="font-semibold">Bands:</span>
          {scene.bands.slice(0, 8).map((b) => (
            <span key={b} className="px-1.5 py-0.2 bg-slate-200/70 dark:bg-earth-900 rounded font-mono">
              {b}
            </span>
          ))}
          {scene.bands.length > 8 && <span>+{scene.bands.length - 8} more</span>}
        </div>
      )}

      {/* Download Credentials Warning */}
      {scene.download_requires_credentials && !scene.is_already_ingested && (
        <div className="flex items-center gap-1.5 text-[10px] text-amber-600 dark:text-amber-400 bg-amber-500/10 p-1.5 rounded border border-amber-500/20">
          <Lock className="w-3 h-3 flex-shrink-0" />
          <span>Raster download requires provider credentials in backend .env. Metadata ingestion is supported.</span>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-between gap-2 pt-2 border-t border-slate-200/80 dark:border-slate-800/80">
        {onSelectFootprint && (
          <button
            onClick={() => onSelectFootprint(scene)}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-slate-100 dark:bg-earth-900 text-slate-700 dark:text-slate-300 hover:text-cyan-600 dark:hover:text-cyanGlow-400 border border-slate-200 dark:border-slate-800 transition-colors"
          >
            <Eye className="w-3 h-3" />
            <span>Map Footprint</span>
          </button>
        )}

        <div className="flex items-center gap-1.5 ml-auto">
          {ingestedStatus === 'completed' || scene.is_already_ingested ? (
            <span className="inline-flex items-center gap-1 px-3 py-1 rounded-lg text-[11px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
              <CheckCircle className="w-3 h-3" />
              <span>Available in Catalog</span>
            </span>
          ) : (
            <>
              {/* Metadata-only option if download credentials aren't set */}
              {scene.download_requires_credentials ? (
                <button
                  onClick={() => handleIngestClick(false)}
                  disabled={isIngesting}
                  className="inline-flex items-center gap-1 px-3 py-1 rounded-lg text-[11px] font-semibold bg-cyan-600 hover:bg-cyan-500 text-white transition-colors shadow-sm disabled:opacity-50"
                >
                  <Download className="w-3 h-3" />
                  <span>Ingest Metadata</span>
                </button>
              ) : (
                <button
                  onClick={() => handleIngestClick(true)}
                  disabled={isIngesting}
                  className="inline-flex items-center gap-1 px-3 py-1 rounded-lg text-[11px] font-semibold bg-cyan-600 hover:bg-cyan-500 text-white transition-colors shadow-sm disabled:opacity-50"
                >
                  <Download className="w-3 h-3" />
                  <span>Ingest Scene</span>
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
