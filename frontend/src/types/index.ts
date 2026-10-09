export type UserRole = 
  | 'Citizen'
  | 'Government'
  | 'Municipality'
  | 'NGO'
  | 'Researcher'
  | 'Administrator';

export type EnvironmentalDomainId =
  | 'forest'
  | 'water-bodies'
  | 'mountains'
  | 'plains'
  | 'coastal-areas'
  | 'urban-areas'
  | 'urban-heat'
  | 'agriculture'
  | 'deserts';

export interface EnvironmentalDomain {
  id: EnvironmentalDomainId;
  name: string;
  category: string;
  iconName: string;
  description: string;
  status: 'Stable' | 'Vulnerable' | 'Critical Risk' | 'Monitoring';
  keyIndicator: string;
  indicatorValue: string;
  changeRate: string;
  primaryRisk: string;
  affectedRegionsCount: number;
}

export interface ClimateLocation {
  id: string;
  name: string;
  region: string;
  country: string;
  coordinates: [number, number]; // [lat, lng]
  zoom: number;
  landform: string;
  elevation: string;
  dominantDomain: EnvironmentalDomainId;
  riskLevel: 'Low' | 'Moderate' | 'High' | 'Severe';
  satelliteSensors: string[];
  lastObservation: string;
  description: string;
  keyStats: {
    label: string;
    value: string;
    trend: 'up' | 'down' | 'stable';
  }[];
}

export interface ClimateRiskCategory {
  id: string;
  name: string;
  score: number; // 0 - 100
  level: 'Low' | 'Moderate' | 'High' | 'Critical';
  trend: 'Increasing' | 'Stable' | 'Decreasing';
  contributingFactors: string[];
}

export interface RecommendedAction {
  id: string;
  title: string;
  description: string;
  category: 'Mitigation' | 'Adaptation' | 'Resilience' | 'Policy' | 'Community';
  targetRoles: UserRole[];
  impactScore: 'High' | 'Medium' | 'Critical';
  timeframe: 'Immediate (0-6m)' | 'Medium Term (1-3y)' | 'Long Term (5y+)';
  estimatedCost: string;
  domainId: EnvironmentalDomainId;
}

export interface SimulationScenario {
  id: string;
  name: string;
  tempIncrease: number; // e.g. +1.5, +2.0, +3.0 C
  seaLevelRise: number; // meters
  deforestationRate: number; // %
  urbanizationPace: number; // %
}

// ─── Phase 4: Earth Observation Satellite Pipeline Types ────────────────────

export type IngestionStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface EOScene {
  scene_id: string;
  provider: 'copernicus' | 'usgs' | 'up42' | string;
  satellite: string;
  sensor: string;
  acquisition_date: string;
  cloud_cover?: number;
  bbox: [number, number, number, number]; // [min_lon, min_lat, max_lon, max_lat]
  footprint_geojson?: any;
  resolution_m?: number;
  source_url?: string;
  thumbnail_url?: string;
  processing_level?: string;
  bands?: string[];
  metadata?: Record<string, any>;
  download_requires_credentials?: boolean;
  is_already_ingested?: boolean;
}

export interface SceneSearchParams {
  date_from: string;
  date_to: string;
  lat?: number;
  lon?: number;
  bbox?: [number, number, number, number];
  satellite?: string;
  cloud_cover_max?: number;
  providers?: string[];
  limit?: number;
}

export interface SceneIngestionRequest {
  scene_id: string;
  provider: string;
  satellite?: string;
  sensor?: string;
  acquisition_date: string;
  cloud_cover?: number;
  resolution_m?: number;
  bbox?: [number, number, number, number];
  footprint_geojson?: any;
  source_url?: string;
  thumbnail_url?: string;
  bands?: string[];
  metadata?: Record<string, any>;
  location_id?: string;
  domain_id?: string;
  download_raster?: boolean;
}

export interface IngestionStatusResponse {
  id: number;
  scene_id: string;
  provider: string;
  ingestion_status: IngestionStatus;
  ingestion_error?: string;
  ingested_at?: string;
  file_path?: string;
  file_size_bytes?: number;
}

export interface SceneFootprintResponse {
  id: number;
  scene_id: string;
  provider: string;
  satellite?: string;
  sensor: string;
  acquisition_date: string;
  bbox?: [number, number, number, number];
  footprint_geojson?: any;
  thumbnail_url?: string;
}

// ─── Phase 5A: Earth Observation Data Processing Types ──────────────────────

export type CompositeMode = 'RGB' | 'FALSE_COLOR' | 'SWIR';

export interface ProcessingRequest {
  index_name: string; // "NDVI" | "NDWI" | "NDBI" | "LST"
  location_id?: string;
}

export interface ProcessedImageOut {
  id: number;
  scene_id: number;
  index_name: string;
  file_path: string;
  status: 'processing' | 'completed' | 'failed';
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface SpatialFeatureOut {
  id: number;
  location_id: string;
  processed_image_id?: number;
  index_name: string;
  mean_value?: number;
  min_value?: number;
  max_value?: number;
  std_dev?: number;
  valid_pixels?: number;
  created_at: string;
}

export interface HistogramData {
  index_name: string;
  counts: number[];
  bin_edges: number[];
  bin_midpoints: number[];
  total_pixels: number;
  num_bins: number;
}

// ─── Phase 5B: ML Change Detection Types ────────────────────────────────────

/** Ingested scene with completed Phase 5A processing — available for change detection */
export interface IngestedSceneForML {
  db_id: number;
  scene_id: string;
  satellite: string;
  sensor: string;
  acquisition_date: string;
  cloud_cover?: number;
  resolution_m?: number;
  available_indices: string[];
}

export interface ChangeDetectionRequest {
  location_id?: string;
  before_scene_db_id: number;
  after_scene_db_id: number;
  k_sigma?: number;
  min_change_area_px?: number;
}

export interface MLJobSubmitResponse {
  job_id: string;
  status: 'pending';
  message: string;
  poll_url: string;
}

export interface ChangeCategoryOut {
  category: string;       // e.g. 'vegetation_loss', 'water_gain'
  pixel_count: number;
  area_km2: number;
  description: string;
  label_value: number;
}

export interface AlgorithmInfoOut {
  name: string;           // 'MISCD'
  version: string;        // '1.0.0'
  algorithm_type: string; // 'threshold_based_spectral_analysis'
  indices_used: string[];
  parameters: Record<string, unknown>;
}

export interface EvaluationMetricsOut {
  /** TP / (TP + FP). null if no changed pixels predicted. */
  precision?: number | null;
  /** TP / (TP + FN). null if no actual positives in GT. */
  recall?: number | null;
  f1_score?: number | null;
  /** Intersection over Union: TP / (TP + FP + FN). */
  iou?: number | null;
  accuracy?: number | null;
  true_positives: number;
  true_negatives: number;
  false_positives: number;
  false_negatives: number;
  evaluated_pixels: number;
  changed_in_gt: number;
  changed_in_pred: number;
  ground_truth_source: string;
  notes: string;
}

export interface MLResultOut {
  id: string;
  job_id: string;
  algorithm: AlgorithmInfoOut;
  change_map_url?: string;
  change_map_crs?: string;
  change_map_bounds?: [number, number, number, number];
  total_area_km2?: number;
  changed_area_km2?: number;
  changed_pct?: number;
  /** SNR-based metric [0–1]. NOT model accuracy. */
  signal_quality_index?: number;
  change_categories: ChangeCategoryOut[];
  /**
   * Pixel-level evaluation metrics. null in all normal unsupervised runs.
   * Populated only when a labelled ground-truth mask is supplied.
   */
  evaluation_metrics?: EvaluationMetricsOut | null;
  before_scene_id?: string;
  after_scene_id?: string;
  before_acquisition_date?: string;
  after_acquisition_date?: string;
  valid_pixel_fraction?: number;
  created_at?: string;
}

export type MLJobStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface MLJobOut {
  id: string;
  location_id?: string;
  analysis_type: string;
  status: MLJobStatus;
  before_scene_id: string;
  after_scene_id: string;
  error_message?: string;
  created_at?: string;
  started_at?: string;
  completed_at?: string;
  result?: MLResultOut;
}
