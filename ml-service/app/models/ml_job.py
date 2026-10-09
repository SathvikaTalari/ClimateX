"""
ORM models for the ML/Change-Detection service — Phase 5B.

Two tables are created in the shared PostgreSQL database:
  - ml_analysis_jobs : tracks the lifecycle of each analysis request
  - ml_results       : stores outputs, statistics, and full provenance

These tables are ML-service-owned and written only by this service.
The backend reads them via the proxy layer (or could join them for reporting).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Float, DateTime, Text, ForeignKey, Integer, Index,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


def _new_uuid() -> str:
    return str(uuid.uuid4())


class MLAnalysisJob(Base):
    """
    Tracks a single change-detection analysis request from submission to completion.

    Lifecycle: pending → running → completed | failed

    Design note: a future worker-queue migration only needs to replace the
    asyncio.create_task() call in the router; this model and all downstream
    code remain unchanged.
    """
    __tablename__ = "ml_analysis_jobs"

    id = Column(
        UUID(as_uuid=False), primary_key=True, default=_new_uuid, index=True
    )

    # ── Request identity ─────────────────────────────────────────────────────
    location_id = Column(String(32), nullable=True, index=True)   # ClimateX location ID
    analysis_type = Column(
        String(64), nullable=False, default="change_detection", index=True
    )

    # ── Scene references (FK to backend satellite_scenes.id) ─────────────────
    # Stored as integer IDs — we don't declare a FK here so the ML service
    # remains loosely coupled to the backend schema.
    before_scene_db_id = Column(Integer, nullable=False)
    after_scene_db_id = Column(Integer, nullable=False)
    before_scene_id = Column(String(256), nullable=False)   # provider scene_id string
    after_scene_id = Column(String(256), nullable=False)

    # ── Job lifecycle ────────────────────────────────────────────────────────
    status = Column(
        String(16), nullable=False, default="pending", index=True
    )  # pending | running | completed | failed
    error_message = Column(Text, nullable=True)

    # ── Parameters bag (k_sigma, min_area_px, index selection, etc.) ─────────
    parameters = Column(JSONB, nullable=True, default=dict)

    # ── Timestamps ───────────────────────────────────────────────────────────
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────
    result = relationship(
        "MLResult", back_populates="job", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_ml_jobs_location_type", "location_id", "analysis_type"),
        Index("ix_ml_jobs_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<MLAnalysisJob id={self.id!r} type={self.analysis_type!r} "
            f"status={self.status!r}>"
        )


class MLResult(Base):
    """
    Stores the output of a completed change-detection analysis.

    Fields follow scientific naming conventions:
      - algorithm_name/version/type: honest description of what ran
      - signal_quality_index: SNR-based metric (not "accuracy" or "confidence")
      - change_statistics: area/percentage by category
      - provenance: complete audit trail (inputs, alignment, masking, algorithm)
    """
    __tablename__ = "ml_results"

    id = Column(
        UUID(as_uuid=False), primary_key=True, default=_new_uuid, index=True
    )
    job_id = Column(
        UUID(as_uuid=False),
        ForeignKey("ml_analysis_jobs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # ── Algorithm identity ────────────────────────────────────────────────────
    algorithm_name = Column(String(128), nullable=False)      # "MISCD"
    algorithm_version = Column(String(32), nullable=False)    # "1.0.0"
    algorithm_type = Column(String(64), nullable=False)       # "threshold_based_spectral_analysis"

    # ── Output raster ────────────────────────────────────────────────────────
    # Path relative to ml_storage_path root
    change_map_path = Column(Text, nullable=True)
    # CRS of the output raster
    change_map_crs = Column(String(64), nullable=True)
    # Bounding box [min_lon, min_lat, max_lon, max_lat] in EPSG:4326
    change_map_bounds = Column(JSONB, nullable=True)

    # ── Summary statistics (top-level for easy querying) ─────────────────────
    total_area_km2 = Column(Float, nullable=True)
    changed_area_km2 = Column(Float, nullable=True)
    changed_pct = Column(Float, nullable=True)

    # ── Signal Quality Index [0–1] ────────────────────────────────────────────
    # SNR-based metric: mean(|Δ|_changed) / (σ_background + ε)
    # NOT a model accuracy or confidence score.
    signal_quality_index = Column(Float, nullable=True)

    # ── Detailed change statistics by category ────────────────────────────────
    # {"vegetation_loss_km2": ..., "water_gain_km2": ..., "urban_gain_km2": ...}
    change_statistics = Column(JSONB, nullable=True, default=dict)

    # ── Evaluation metrics (populated only when ground truth is available) ──────
    # Keys: precision, recall, f1_score, iou, accuracy, true_positives,
    #       true_negatives, false_positives, false_negatives, evaluated_pixels,
    #       changed_in_gt, changed_in_pred, ground_truth_source, notes
    # null  = no ground-truth mask supplied (normal production case)
    evaluation_metrics = Column(JSONB, nullable=True, default=None)

    # Path to ground-truth binary mask (relative to eo_storage_root).
    # null = no GT available; set when a user supplies a reference mask.
    ground_truth_path = Column(Text, nullable=True)

    # ── Full provenance ────────────────────────────────────────────────────────
    # Complete audit trail: algorithm params, inputs, alignment, masking details
    provenance = Column(JSONB, nullable=True, default=dict)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    job = relationship("MLAnalysisJob", back_populates="result")

    def __repr__(self) -> str:
        return (
            f"<MLResult id={self.id!r} algorithm={self.algorithm_name!r} "
            f"changed_pct={self.changed_pct!r}>"
        )
