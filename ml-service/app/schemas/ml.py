"""
Pydantic schemas for the ML service API — Phase 5B.

Field names follow scientific conventions:
  - algorithm_type: "threshold_based_spectral_analysis" (never "ml_model")
  - signal_quality_index: SNR-based metric (never "accuracy" or "confidence")
  - evaluation_metrics: null unless a ground-truth mask was supplied
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─── Request Schemas ──────────────────────────────────────────────────────────

class ChangeDetectionRequest(BaseModel):
    """
    Request body for POST /api/v1/ml/change-detection.

    The caller provides DB integer IDs (from the backend satellite_scenes table)
    for the before and after scenes.  The ML service resolves the corresponding
    Phase 5A processed rasters from the shared database.
    """
    location_id: Optional[str] = Field(
        None,
        description="ClimateX location ID (e.g. 'hyderabad') — used for provenance only.",
    )
    before_scene_db_id: int = Field(
        ...,
        description="Integer primary key of the 'before' scene in satellite_scenes.",
    )
    after_scene_db_id: int = Field(
        ...,
        description="Integer primary key of the 'after' scene in satellite_scenes.",
    )
    # Optional parameter overrides (fall back to service config defaults)
    k_sigma: Optional[float] = Field(
        None,
        ge=0.5,
        le=5.0,
        description=(
            "Detection threshold multiplier (μ ± k·σ). "
            "Lower = more sensitive; higher = more conservative. Default: 1.5."
        ),
    )
    min_change_area_px: Optional[int] = Field(
        None,
        ge=1,
        le=1000,
        description="Minimum connected component size (pixels) to keep. Default: 9.",
    )


# ─── Response Schemas ─────────────────────────────────────────────────────────

class ChangeCategoryOut(BaseModel):
    """Statistics for one detected change category."""
    category: str = Field(..., description="e.g. 'vegetation_loss', 'water_gain'")
    pixel_count: int
    area_km2: float
    description: str
    label_value: int = Field(
        ..., description="Pixel value in the change-map raster for this category."
    )


class AlgorithmInfoOut(BaseModel):
    """Algorithm identity — never claims trained-model accuracy."""
    name: str = Field(..., description="e.g. 'MISCD'")
    version: str = Field(..., description="e.g. '1.0.0'")
    algorithm_type: str = Field(
        ...,
        description=(
            "Always 'threshold_based_spectral_analysis' for the current implementation. "
            "Future trained models will use 'supervised_classification'."
        ),
    )
    indices_used: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class EvaluationMetricsOut(BaseModel):
    """
    Pixel-level evaluation metrics against a labelled ground-truth mask.

    All metric values are in [0, 1].  A value of ``null`` means the metric
    could not be computed (e.g., zero denominator — no positive predictions).

    This field is ``null`` in normal production runs (unsupervised analysis
    with no ground truth).  It is populated only when a reference mask is
    supplied, for example during benchmarking on OSCD or LEVIR-CD.
    """
    # ── Core metrics [0, 1] ───────────────────────────────────────────────────
    precision: Optional[float] = Field(
        None,
        description="TP / (TP + FP). Null if no changed pixels predicted.",
    )
    recall: Optional[float] = Field(
        None,
        description="TP / (TP + FN). Null if no actual positives in GT.",
    )
    f1_score: Optional[float] = Field(
        None,
        description="Harmonic mean of precision and recall.",
    )
    iou: Optional[float] = Field(
        None,
        description="Intersection over Union (Jaccard index): TP / (TP + FP + FN).",
    )
    accuracy: Optional[float] = Field(
        None,
        description="(TP + TN) / total_valid_pixels.",
    )

    # ── Confusion matrix ──────────────────────────────────────────────────────
    true_positives: int = 0
    true_negatives: int = 0
    false_positives: int = 0
    false_negatives: int = 0

    # ── Coverage ─────────────────────────────────────────────────────────────
    evaluated_pixels: int = Field(0, description="Valid pixels included in evaluation.")
    changed_in_gt: int = Field(0, description="Changed pixels in ground-truth mask.")
    changed_in_pred: int = Field(0, description="Changed pixels in prediction.")

    # ── Provenance ────────────────────────────────────────────────────────────
    ground_truth_source: str = Field("", description="Dataset name or file path of the GT mask.")
    notes: str = ""

    model_config = {"from_attributes": True}


class MLResultOut(BaseModel):
    """Full result for a completed change-detection job."""
    id: str
    job_id: str

    # Algorithm identity
    algorithm: AlgorithmInfoOut

    # Raster outputs
    change_map_url: Optional[str] = Field(
        None,
        description="URL to download the change-map GeoTIFF file.",
    )
    change_map_crs: Optional[str] = None
    change_map_bounds: Optional[List[float]] = Field(
        None, description="[min_lon, min_lat, max_lon, max_lat] in EPSG:4326."
    )

    # Summary statistics
    total_area_km2: Optional[float] = None
    changed_area_km2: Optional[float] = None
    changed_pct: Optional[float] = None

    # Signal quality (NOT model accuracy)
    signal_quality_index: Optional[float] = Field(
        None,
        description=(
            "Signal Quality Index [0–1]: measures how clearly detected changes "
            "stand out above background noise (SNR-based). "
            "NOT a model accuracy or classification confidence score."
        ),
    )

    # Per-category breakdown
    change_categories: List[ChangeCategoryOut] = Field(default_factory=list)

    # Evaluation metrics (null unless ground truth was supplied)
    evaluation_metrics: Optional[EvaluationMetricsOut] = Field(
        None,
        description=(
            "Pixel-level evaluation metrics (Precision/Recall/F1/IoU/Accuracy). "
            "null in normal unsupervised runs — populated only when a labelled "
            "ground-truth mask is supplied for benchmarking."
        ),
    )

    # Source scenes
    before_scene_id: Optional[str] = None
    after_scene_id: Optional[str] = None
    before_acquisition_date: Optional[str] = None
    after_acquisition_date: Optional[str] = None

    # Processing metadata
    valid_pixel_fraction: Optional[float] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MLJobOut(BaseModel):
    """Job status response."""
    id: str
    location_id: Optional[str] = None
    analysis_type: str
    status: str = Field(
        ...,
        description="pending | running | completed | failed"
    )
    before_scene_id: str
    after_scene_id: str
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Populated when status == "completed"
    result: Optional[MLResultOut] = None

    model_config = {"from_attributes": True}


class MLJobSubmitResponse(BaseModel):
    """Immediate response after submitting a change-detection request."""
    job_id: str
    status: str = "pending"
    message: str
    poll_url: str = Field(
        ..., description="URL to poll for job status."
    )
