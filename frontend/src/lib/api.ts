/**
 * ClimateX API client
 * Fetches data from the FastAPI backend (/api/v1/*).
 * Falls back gracefully to mock data if the backend is unreachable.
 */

import {
  EnvironmentalDomain,
  ClimateLocation,
  EOScene,
  SceneSearchParams,
  SceneIngestionRequest,
  IngestionStatusResponse,
  SceneFootprintResponse,
} from '../types';
import { ENVIRONMENTAL_DOMAINS, LOCATIONS } from '../data/mockData';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL
  ? `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1`
  : '/api/v1';

// ─── Generic fetch helper ─────────────────────────────────────────────────────

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(options?.headers || {}) },
    cache: 'no-store',
    ...options,
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errJson = await response.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch {}
    throw new Error(`API error ${response.status}: ${errorDetail} [${url}]`);
  }

  return response.json() as Promise<T>;
}

// ─── Health ───────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string;
  environment: string;
  database: string;
  version: string;
}

export async function fetchHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>('/health');
}

// ─── Domains ──────────────────────────────────────────────────────────────────

export async function fetchDomains(): Promise<EnvironmentalDomain[]> {
  try {
    return await apiFetch<EnvironmentalDomain[]>('/domains');
  } catch (error) {
    console.warn('[ClimateX API] fetchDomains failed — using mock data fallback.', error);
    return ENVIRONMENTAL_DOMAINS;
  }
}

export async function fetchDomain(id: string): Promise<EnvironmentalDomain | undefined> {
  try {
    return await apiFetch<EnvironmentalDomain>(`/domains/${id}`);
  } catch (error) {
    console.warn(`[ClimateX API] fetchDomain(${id}) failed — using mock data fallback.`, error);
    return ENVIRONMENTAL_DOMAINS.find((d) => d.id === id);
  }
}

// ─── Locations ────────────────────────────────────────────────────────────────

export interface LocationsFilter {
  domain_id?: string;
  risk_level?: string;
}

export async function fetchLocations(filter?: LocationsFilter): Promise<ClimateLocation[]> {
  try {
    const params = new URLSearchParams();
    if (filter?.domain_id) params.set('domain_id', filter.domain_id);
    if (filter?.risk_level) params.set('risk_level', filter.risk_level);

    const query = params.toString() ? `?${params.toString()}` : '';
    return await apiFetch<ClimateLocation[]>(`/locations${query}`);
  } catch (error) {
    console.warn('[ClimateX API] fetchLocations failed — using mock data fallback.', error);
    return LOCATIONS;
  }
}

export async function fetchLocation(id: string): Promise<ClimateLocation | undefined> {
  try {
    return await apiFetch<ClimateLocation>(`/locations/${id}`);
  } catch (error) {
    console.warn(`[ClimateX API] fetchLocation(${id}) failed — using mock data fallback.`, error);
    return LOCATIONS.find((l) => l.id === id);
  }
}

// ─── Observations ─────────────────────────────────────────────────────────────

export interface ObservationItem {
  id: number;
  metric_name: string;
  metric_value: number;
  unit?: string;
  trend?: 'up' | 'down' | 'stable';
  observed_at: string;
  location_id: string;
  domain_id?: string;
  scene_id?: number;
  created_at: string;
}

export interface ObservationsFilter {
  location_id?: string;
  domain_id?: string;
  metric_name?: string;
  limit?: number;
  offset?: number;
}

export async function fetchObservations(filter?: ObservationsFilter): Promise<ObservationItem[]> {
  try {
    const params = new URLSearchParams();
    if (filter?.location_id) params.set('location_id', filter.location_id);
    if (filter?.domain_id) params.set('domain_id', filter.domain_id);
    if (filter?.metric_name) params.set('metric_name', filter.metric_name);
    if (filter?.limit) params.set('limit', filter.limit.toString());
    if (filter?.offset) params.set('offset', filter.offset.toString());

    const query = params.toString() ? `?${params.toString()}` : '';
    return await apiFetch<ObservationItem[]>(`/observations${query}`);
  } catch (error) {
    console.warn('[ClimateX API] fetchObservations failed.', error);
    return [];
  }
}

// ─── Satellite Scenes ─────────────────────────────────────────────────────────

export interface SatelliteSceneItem {
  id: number;
  scene_id: string;
  provider?: string;
  satellite?: string;
  sensor: string;
  acquisition_date: string;
  cloud_cover?: number;
  resolution_m?: number;
  bbox?: [number, number, number, number];
  source_url?: string;
  file_path?: string;
  file_size_bytes?: number;
  crs?: string;
  bands?: string[];
  provenance?: Record<string, any>;
  ingestion_status?: string;
  ingestion_error?: string;
  ingested_at?: string;
  scene_metadata?: Record<string, any>;
  location_id?: string;
  domain_id?: string;
  created_at: string;
}

export interface SatelliteScenesFilter {
  location_id?: string;
  domain_id?: string;
  provider?: string;
  sensor?: string;
  satellite?: string;
  status?: string;
  limit?: number;
  offset?: number;
}

export async function fetchSatelliteScenes(filter?: SatelliteScenesFilter): Promise<SatelliteSceneItem[]> {
  try {
    const params = new URLSearchParams();
    if (filter?.location_id) params.set('location_id', filter.location_id);
    if (filter?.domain_id) params.set('domain_id', filter.domain_id);
    if (filter?.provider) params.set('provider', filter.provider);
    if (filter?.sensor) params.set('sensor', filter.sensor);
    if (filter?.satellite) params.set('satellite', filter.satellite);
    if (filter?.status) params.set('status', filter.status);
    if (filter?.limit) params.set('limit', filter.limit.toString());
    if (filter?.offset) params.set('offset', filter.offset.toString());

    const query = params.toString() ? `?${params.toString()}` : '';
    return await apiFetch<SatelliteSceneItem[]>(`/satellite-scenes${query}`);
  } catch (error) {
    console.warn('[ClimateX API] fetchSatelliteScenes failed.', error);
    return [];
  }
}

// ─── Phase 4 EO Pipeline API Endpoints ────────────────────────────────────────

/**
 * Searches real satellite providers (Copernicus STAC, USGS M2M, UP42).
 */
export async function searchSatelliteScenes(params: SceneSearchParams): Promise<EOScene[]> {
  return apiFetch<EOScene[]>('/satellite-scenes/search', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

/**
 * Triggers ingestion for a satellite scene.
 */
export async function ingestSatelliteScene(req: SceneIngestionRequest): Promise<SatelliteSceneItem> {
  return apiFetch<SatelliteSceneItem>('/satellite-scenes/ingest', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

/**
 * Polls ingestion status for a scene by DB ID or scene_id string.
 */
export async function fetchIngestionStatus(sceneIdentifier: string | number): Promise<IngestionStatusResponse> {
  return apiFetch<IngestionStatusResponse>(`/satellite-scenes/ingestion/${sceneIdentifier}/status`);
}

/**
 * Retrieves spatial footprint polygon (GeoJSON) and bounding box for a scene.
 */
export async function fetchSceneFootprint(sceneIdentifier: string | number): Promise<SceneFootprintResponse> {
  return apiFetch<SceneFootprintResponse>(`/satellite-scenes/${sceneIdentifier}/footprint`);
}

/**
 * Retrieves satellite scenes covering a location ID or coordinate point.
 */
export async function fetchScenesByLocation(
  locationId?: string,
  lat?: number,
  lon?: number,
  limit: number = 20
): Promise<SatelliteSceneItem[]> {
  const params = new URLSearchParams();
  if (locationId) params.set('location_id', locationId);
  if (lat !== undefined) params.set('lat', lat.toString());
  if (lon !== undefined) params.set('lon', lon.toString());
  params.set('limit', limit.toString());

  return apiFetch<SatelliteSceneItem[]>(`/satellite-scenes/by-location?${params.toString()}`);
}

// ─── Phase 5A EO Processing API Endpoints ─────────────────────────────────────

import { ProcessingRequest, ProcessedImageOut, SpatialFeatureOut, HistogramData, CompositeMode } from '../types';

export async function processScene(
  sceneIdentifier: string | number,
  req: ProcessingRequest
): Promise<ProcessedImageOut> {
  return apiFetch<ProcessedImageOut>(`/satellite-scenes/${sceneIdentifier}/process`, {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

export async function fetchProcessingStatus(
  sceneIdentifier: string | number
): Promise<ProcessedImageOut[]> {
  return apiFetch<ProcessedImageOut[]>(`/satellite-scenes/${sceneIdentifier}/processing-status`);
}

export async function fetchLocationSpatialFeatures(
  locationId: string,
  indexName?: string
): Promise<SpatialFeatureOut[]> {
  const query = indexName ? `?index_name=${indexName}` : '';
  return apiFetch<SpatialFeatureOut[]>(`/locations/${locationId}/spatial-features${query}`);
}

/** Returns the URL to stream a composite PNG (RGB / FALSE_COLOR / SWIR) for a scene. */
export function getCompositeUrl(
  sceneIdentifier: string | number,
  mode: CompositeMode = 'RGB',
  locationId?: string
): string {
  const params = new URLSearchParams({ mode, _t: Date.now().toString() });
  if (locationId) params.set('location_id', locationId);
  return `${API_BASE}/satellite-scenes/${sceneIdentifier}/composite?${params.toString()}`;
}

/** Fetch histogram data for a processed image by ID. */
export async function fetchProcessedImageHistogram(
  imageId: number,
  nBins: number = 32
): Promise<HistogramData> {
  return apiFetch<HistogramData>(`/processed-images/${imageId}/histogram?n_bins=${nBins}`);
}

/** Returns a URL to download spatial features as GeoJSON or CSV. */
export function getSpatialFeaturesExportUrl(
  locationId: string,
  format: 'geojson' | 'csv' = 'geojson',
  indexName?: string
): string {
  const params = new URLSearchParams({ format });
  if (indexName) params.set('index_name', indexName);
  return `${API_BASE}/locations/${locationId}/spatial-features/export?${params.toString()}`;
}

// ─── Phase 5B: ML Change Detection API Endpoints ──────────────────────────────

import {
  ChangeDetectionRequest,
  MLJobSubmitResponse,
  MLJobOut,
  MLResultOut,
  IngestedSceneForML,
} from '../types';

/** List scenes that have completed Phase 5A processing and are ready for change detection. */
export async function fetchIngestedScenesForML(
  locationId: string
): Promise<IngestedSceneForML[]> {
  try {
    return await apiFetch<IngestedSceneForML[]>(`/ml/scenes/${locationId}/ingested`);
  } catch (error) {
    console.warn('[ClimateX API] fetchIngestedScenesForML failed.', error);
    return [];
  }
}

/** Submit a change-detection analysis job. Returns immediately with job_id. */
export async function submitChangeDetection(
  req: ChangeDetectionRequest
): Promise<MLJobSubmitResponse> {
  return apiFetch<MLJobSubmitResponse>('/ml/change-detection', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

/** Poll job status. When status === 'completed', result is embedded in the response. */
export async function fetchMLJob(jobId: string): Promise<MLJobOut> {
  return apiFetch<MLJobOut>(`/ml/jobs/${jobId}`);
}

/** Get the full result for a completed job by result ID. */
export async function fetchMLResult(resultId: string): Promise<MLResultOut> {
  return apiFetch<MLResultOut>(`/ml/results/${resultId}`);
}

/**
 * Generate synthetic demo satellite scenes and immediately run change detection.
 * No real satellite ingestion or Phase 5A processing required.
 * Returns a job_id to poll for results.
 */
export async function runDemoAnalysis(
  locationId: string
): Promise<{ job_id: string; status: string; message: string; demo: boolean }> {
  return apiFetch(`/ml/demo/${locationId}`, { method: 'POST' });
}
