"""
ML Service Router — Phase 5B.

Endpoints
---------
POST /api/v1/ml/change-detection          Submit a change-detection job
GET  /api/v1/ml/jobs/{job_id}             Poll job status (+ result when done)
GET  /api/v1/ml/jobs/{job_id}/result      Convenience: get result by job ID
GET  /api/v1/ml/results/{result_id}       Get result by result ID
GET  /api/v1/ml/change-maps/{job_id}/file Download change-map GeoTIFF

Design
------
Jobs are executed as asyncio background tasks.  The client polls GET /jobs/{id}
every few seconds.  When status == "completed", the full result is embedded
in the response to avoid a second round-trip.

To migrate to a worker queue: replace asyncio.create_task() with
queue.enqueue() here — nothing else changes.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models.ml_job import MLAnalysisJob, MLResult
from ..pipeline.runner import run_change_detection_job
from ..pipeline.demo_generator import generate_demo_scenes
from ..schemas.ml import (
    ChangeDetectionRequest,
    MLJobOut,
    MLJobSubmitResponse,
    MLResultOut,
    AlgorithmInfoOut,
    ChangeCategoryOut,
    EvaluationMetricsOut,
)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/ml", tags=["ML Change Detection"])
settings = get_settings()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _build_result_out(result: MLResult, request_base_url: str) -> MLResultOut:
    """Convert MLResult ORM row → MLResultOut schema."""
    prov = result.provenance or {}
    algo_prov = prov.get("algorithm", {})
    inputs = prov.get("inputs", {})
    masking = prov.get("masking", {})

    before_info = inputs.get("before", {})
    after_info = inputs.get("after", {})

    # Build change_map download URL
    change_map_url = (
        f"{request_base_url}/api/v1/ml/change-maps/{result.job_id}/file"
        if result.change_map_path else None
    )

    # Per-category list
    categories = [
        ChangeCategoryOut(
            category=cat_name,
            pixel_count=cat_data.get("pixel_count", 0),
            area_km2=cat_data.get("area_km2", 0.0),
            description=cat_data.get("description", ""),
            label_value=cat_data.get("label_value", 0),
        )
        for cat_name, cat_data in (result.change_statistics or {}).items()
    ]
    # Sort by area descending
    categories.sort(key=lambda c: c.area_km2, reverse=True)

    # Evaluation metrics (null unless GT mask was supplied)
    eval_metrics_out = None
    if result.evaluation_metrics:
        eval_metrics_out = EvaluationMetricsOut(**result.evaluation_metrics)

    return MLResultOut(
        id=result.id,
        job_id=result.job_id,
        algorithm=AlgorithmInfoOut(
            name=result.algorithm_name,
            version=result.algorithm_version,
            algorithm_type=result.algorithm_type,
            indices_used=algo_prov.get("indices_used", []),
            parameters=algo_prov.get("parameters", {}),
        ),
        change_map_url=change_map_url,
        change_map_crs=result.change_map_crs,
        change_map_bounds=result.change_map_bounds,
        total_area_km2=result.total_area_km2,
        changed_area_km2=result.changed_area_km2,
        changed_pct=result.changed_pct,
        signal_quality_index=result.signal_quality_index,
        change_categories=categories,
        evaluation_metrics=eval_metrics_out,
        before_scene_id=before_info.get("scene_id"),
        after_scene_id=after_info.get("scene_id"),
        before_acquisition_date=before_info.get("acquisition_date"),
        after_acquisition_date=after_info.get("acquisition_date"),
        valid_pixel_fraction=masking.get("valid_pixel_fraction"),
        created_at=result.created_at,
    )


def _build_job_out(
    job: MLAnalysisJob,
    result: Optional[MLResult],
    request_base_url: str,
) -> MLJobOut:
    """Convert MLAnalysisJob (+ optional MLResult) → MLJobOut schema."""
    result_out = None
    if result and job.status == "completed":
        result_out = _build_result_out(result, request_base_url)

    return MLJobOut(
        id=job.id,
        location_id=job.location_id,
        analysis_type=job.analysis_type,
        status=job.status,
        before_scene_id=job.before_scene_id,
        after_scene_id=job.after_scene_id,
        error_message=job.error_message,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        result=result_out,
    )


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post(
    "/change-detection",
    response_model=MLJobSubmitResponse,
    status_code=202,
    summary="Submit a satellite change-detection analysis job",
    description=(
        "Submits a spectral change-detection job comparing two satellite scenes. "
        "Processing runs asynchronously — poll GET /jobs/{job_id} for status. "
        "Both scenes must have completed Phase 5A EO processing (NDVI/NDWI/NDBI)."
    ),
)
async def submit_change_detection(
    req: ChangeDetectionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # Validate that before ≠ after
    if req.before_scene_db_id == req.after_scene_db_id:
        raise HTTPException(
            status_code=400,
            detail="before_scene_db_id and after_scene_db_id must be different scenes.",
        )

    # Build parameters dict
    params = {}
    if req.k_sigma is not None:
        params["k_sigma"] = req.k_sigma
    if req.min_change_area_px is not None:
        params["min_change_area_px"] = req.min_change_area_px

    # Resolve scene_id strings for provenance (read from shared DB)
    from sqlalchemy import text
    def get_scene_id(db_id: int) -> str:
        row = db.execute(
            text("SELECT scene_id FROM satellite_scenes WHERE id = :sid"),
            {"sid": db_id},
        ).fetchone()
        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Satellite scene with DB id={db_id} not found.",
            )
        return row[0]

    before_scene_id = get_scene_id(req.before_scene_db_id)
    after_scene_id = get_scene_id(req.after_scene_db_id)

    # Create job record
    job = MLAnalysisJob(
        location_id=req.location_id,
        analysis_type="change_detection",
        before_scene_db_id=req.before_scene_db_id,
        after_scene_db_id=req.after_scene_db_id,
        before_scene_id=before_scene_id,
        after_scene_id=after_scene_id,
        status="pending",
        parameters=params if params else None,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    job_id = job.id
    log.info(
        "Job %s created: before=%s after=%s location=%s",
        job_id, before_scene_id, after_scene_id, req.location_id,
    )

    # Launch background task
    background_tasks.add_task(run_change_detection_job, job_id)

    return MLJobSubmitResponse(
        job_id=job_id,
        status="pending",
        message=(
            "Change detection job submitted. "
            "Poll the poll_url every 2–5 seconds for status updates."
        ),
        poll_url=f"/api/v1/ml/jobs/{job_id}",
    )


@router.get(
    "/jobs/{job_id}",
    response_model=MLJobOut,
    summary="Get job status and result (when completed)",
)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    request_base_url: str = Query(
        "http://localhost:8001",
        description="Base URL of the ML service (used to build change_map_url).",
        include_in_schema=False,
    ),
):
    job = db.query(MLAnalysisJob).filter(MLAnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    result = None
    if job.status == "completed":
        result = db.query(MLResult).filter(MLResult.job_id == job_id).first()

    return _build_job_out(job, result, request_base_url)


@router.get(
    "/jobs/{job_id}/result",
    response_model=MLResultOut,
    summary="Get the full result for a completed job",
)
def get_job_result(
    job_id: str,
    db: Session = Depends(get_db),
    request_base_url: str = Query(
        "http://localhost:8001",
        include_in_schema=False,
    ),
):
    job = db.query(MLAnalysisJob).filter(MLAnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    if job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job is not yet completed (status: {job.status}).",
        )

    result = db.query(MLResult).filter(MLResult.job_id == job_id).first()
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Result record not found even though job is completed.",
        )

    return _build_result_out(result, request_base_url)


@router.get(
    "/results/{result_id}",
    response_model=MLResultOut,
    summary="Get a specific result by its own ID",
)
def get_result(
    result_id: str,
    db: Session = Depends(get_db),
    request_base_url: str = Query(
        "http://localhost:8001",
        include_in_schema=False,
    ),
):
    result = db.query(MLResult).filter(MLResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail=f"Result '{result_id}' not found.")
    return _build_result_out(result, request_base_url)


@router.get(
    "/change-maps/{job_id}/file",
    summary="Download the change-map GeoTIFF for a completed job",
)
def get_change_map_file(
    job_id: str,
    db: Session = Depends(get_db),
):
    """
    Streams the labelled change-map GeoTIFF (uint8, LZW-compressed COG).

    Pixel legend:
      0   = No significant change
      1   = Water body change
      2   = Vegetation / forest change
      3   = Built-up / urban change
      255 = Masked (nodata / cloud / shadow)
    """
    result = db.query(MLResult).filter(MLResult.job_id == job_id).first()
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No completed result found for job '{job_id}'.",
        )
    if not result.change_map_path:
        raise HTTPException(status_code=404, detail="Change map path not recorded.")

    # change_map_path is relative to eo_storage_root
    eo_root = Path(settings.eo_storage_path)
    full_path = eo_root / result.change_map_path
    if not full_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Change map GeoTIFF not found on disk.",
        )

    return FileResponse(
        path=str(full_path),
        media_type="image/tiff",
        filename=f"change_map_{job_id}.tif",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@router.get(
    "/change-maps/{job_id}/preview",
    summary="Get colored PNG preview of the change map",
)
def get_change_map_preview(
    job_id: str,
    db: Session = Depends(get_db),
):
    """
    Streams a 4-band RGBA PNG preview with colored category overlays:
      - Blue: Water expansion/contraction
      - Green: Vegetation loss/gain
      - Orange: Built-up/Urban expansion
    """
    result = db.query(MLResult).filter(MLResult.job_id == job_id).first()
    if not result:
        raise HTTPException(status_code=404, detail=f"No result found for job '{job_id}'.")

    eo_root = Path(settings.eo_storage_path)
    ml_root = Path(settings.ml_storage_path)
    png_path = ml_root / f"change_map_{job_id}.png"

    if not png_path.exists():
        # Fallback: if PNG doesn't exist yet, render it from TIFF on demand
        if not result.change_map_path:
            raise HTTPException(status_code=404, detail="Change map path missing.")
        tiff_path = eo_root / result.change_map_path
        if not tiff_path.exists():
            raise HTTPException(status_code=404, detail="Change map GeoTIFF missing.")

        import rasterio
        from ..pipeline.runner import _write_change_map_png
        with rasterio.open(tiff_path) as src:
            arr = src.read(1)
            _write_change_map_png(arr, png_path, bounds_wgs84=result.change_map_bounds)

    return FileResponse(
        path=str(png_path),
        media_type="image/png",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@router.get("/health", include_in_schema=False)
def health():
    return {"service": "ClimateX ML Service", "status": "ok"}


@router.post(
    "/demo/{location_id}",
    status_code=202,
    summary="Run a demo change-detection analysis with synthetic satellite data",
    description=(
        "Generates synthetic before/after satellite scenes with realistic NDVI/NDWI/NDBI rasters "
        "and immediately submits a change-detection job. No real satellite data required. "
        "Demo scenes are labelled provider='demo' and can be deleted at any time."
    ),
)
async def run_demo_analysis(
    location_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    One-click demo — creates synthetic scenes + runs the full MISCD pipeline.

    The synthetic rasters include:
    - Urban expansion (bottom-right quadrant)
    - Water body expansion (top-left)
    - Vegetation recovery (central patch)
    """
    eo_root = Path(settings.eo_storage_path)

    log.info("Demo analysis requested for location=%s", location_id)
    before_db_id, after_db_id, before_scene_id, after_scene_id = generate_demo_scenes(
        db, location_id, eo_root
    )

    job = MLAnalysisJob(
        location_id=location_id,
        analysis_type="change_detection",
        before_scene_db_id=before_db_id,
        after_scene_db_id=after_db_id,
        before_scene_id=before_scene_id,
        after_scene_id=after_scene_id,
        status="pending",
        parameters={"demo": True},
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(run_change_detection_job, job.id)

    log.info("Demo job %s submitted for location=%s", job.id, location_id)
    return {
        "job_id": job.id,
        "status": "pending",
        "message": (
            "Demo analysis started with synthetic satellite data. "
            "Simulated changes: urban expansion, water flooding, vegetation recovery."
        ),
        "poll_url": f"/api/v1/ml/jobs/{job.id}",
        "demo": True,
    }
