"""
Pipeline runner — orchestrates load → detect → write COG → persist to DB.

This module is the only place that ties together:
  data_loader  → change_detection  → raster writer  → database

The router calls `run_change_detection_job()` inside an asyncio task.
To migrate to a worker queue (Celery, RQ, ARQ) in a future phase, only this
call site needs to change; the rest of the pipeline is queue-agnostic.
"""
from __future__ import annotations

import asyncio
import logging
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import rasterio
from rasterio.transform import from_bounds
from sqlalchemy.orm import Session

from .base import CHANGE_MAP_NODATA, ChangeResult
from .change_detection import SpectralThresholdDetector
from .data_loader import NODATA_THRESHOLD, load_multi_index_pairs
from ..config import get_settings
from ..database import SessionLocal
from ..models.ml_job import MLAnalysisJob, MLResult

log = logging.getLogger(__name__)
settings = get_settings()


# ─── COG Writer ───────────────────────────────────────────────────────────────

def _write_change_map_cog(
    change_map: np.ndarray,
    meta: object,
    out_path: Path,
) -> None:
    """
    Write the labelled change map as a uint8 Cloud-Optimised GeoTIFF.

    Pixel values:
      0   = no change
      1   = water
      2   = vegetation
      3   = urban
      255 = nodata / masked
    """
    h, w = change_map.shape
    out_path.parent.mkdir(parents=True, exist_ok=True)

    use_tiling = h >= 16 and w >= 16
    bx = min(256, max(16, (w // 16) * 16)) if w >= 16 else 16
    by = min(256, max(16, (h // 16) * 16)) if h >= 16 else 16

    profile = {
        "driver":    "GTiff",
        "dtype":     "uint8",
        "count":     1,
        "crs":       meta.crs,
        "transform": meta.transform,
        "height":    h,
        "width":     w,
        "nodata":    CHANGE_MAP_NODATA,
        "compress":  "lzw",
    }
    if use_tiling:
        profile.update(tiled=True, blockxsize=bx, blockysize=by)

    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(change_map.astype("uint8"), 1)

def _write_change_map_png(
    change_map: np.ndarray,
    out_path: Path,
    bounds_wgs84: Optional[Tuple[float, float, float, float]] = None,
    bg_img_path: Optional[Path] = None,
) -> None:
    """
    Write a GIS cartographic PNG preview.

    Background priority:
      1. Pre-rendered demo RGB (bg_img_path) — instant, no network.
      2. ESRI World Imagery tiles — fetched in parallel, 2 s per tile,
         max 4 tiles (2x2 grid), 6 s total wall-clock limit.
      3. Dark fallback — if offline or all fetches fail.
    """
    from PIL import Image
    import math
    import urllib.request
    from io import BytesIO
    from concurrent.futures import ThreadPoolExecutor, as_completed

    h, w = change_map.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)

    # ── 1. Fast path: pre-rendered demo/RGB background ───────────────────────
    bg_loaded = False
    if bg_img_path and bg_img_path.exists():
        try:
            bg_img = Image.open(bg_img_path).convert("RGBA").resize((w, h))
            base_bg = np.array(bg_img)
            rgba[..., :3] = base_bg[..., :3]
            rgba[..., 3] = 255
            bg_loaded = True
            log.debug("PNG background loaded from disk: %s", bg_img_path)
        except Exception as exc:
            log.warning("Could not load background image: %s", exc)

    # ── 2. Network path: parallel ESRI tile fetch ────────────────────────────
    if not bg_loaded and bounds_wgs84:
        try:
            min_lon, min_lat, max_lon, max_lat = bounds_wgs84
            max_diff = max(max_lon - min_lon, max_lat - min_lat)
            zoom = int(math.log2(360.0 / max_diff)) + 1 if max_diff > 0 else 13
            zoom = min(15, zoom)  # lower zoom = fewer tiles needed

            n = 2.0 ** zoom
            n_min_x = (min_lon + 180.0) / 360.0 * n
            n_max_x = (max_lon + 180.0) / 360.0 * n
            lat_rad_max = math.radians(max_lat)
            lat_rad_min = math.radians(min_lat)
            n_min_y = (1.0 - math.asinh(math.tan(lat_rad_max)) / math.pi) / 2.0 * n
            n_max_y = (1.0 - math.asinh(math.tan(lat_rad_min)) / math.pi) / 2.0 * n

            tx_min, tx_max = int(math.floor(n_min_x)), int(math.floor(n_max_x))
            ty_min, ty_max = int(math.floor(n_min_y)), int(math.floor(n_max_y))

            # Hard cap: max 2x2 = 4 tiles to bound wall-clock time
            if tx_max - tx_min > 1: tx_max = tx_min + 1
            if ty_max - ty_min > 1: ty_max = ty_min + 1

            tile_coords = [
                (tx, ty)
                for tx in range(tx_min, tx_max + 1)
                for ty in range(ty_min, ty_max + 1)
            ]
            grid_w = (tx_max - tx_min + 1) * 256
            grid_h = (ty_max - ty_min + 1) * 256
            stitched = Image.new("RGBA", (grid_w, grid_h))
            req_headers = {"User-Agent": "Mozilla/5.0"}

            def _fetch_tile(coord):
                tx, ty = coord
                url = (
                    f"https://server.arcgisonline.com/ArcGIS/rest/services/"
                    f"World_Imagery/MapServer/tile/{zoom}/{ty}/{tx}"
                )
                req = urllib.request.Request(url, headers=req_headers)
                with urllib.request.urlopen(req, timeout=2) as resp:  # 2 s per tile
                    return tx, ty, resp.read()

            # Fetch all tiles in parallel; total budget 6 s
            with ThreadPoolExecutor(max_workers=4) as pool:
                futures = {pool.submit(_fetch_tile, coord): coord for coord in tile_coords}
                done = as_completed(futures, timeout=6)
                try:
                    for fut in done:
                        try:
                            tx, ty, tile_data = fut.result()
                            tile_img = Image.open(BytesIO(tile_data)).convert("RGBA")
                            stitched.paste(tile_img, ((tx - tx_min) * 256, (ty - ty_min) * 256))
                        except Exception as tile_exc:
                            log.debug("Tile skipped: %s", tile_exc)
                except Exception:
                    log.warning("Tile pool exceeded budget — using partial result.")

            px_min_lon = n_min_x * 256
            px_max_lon = n_max_x * 256
            px_min_lat = n_max_y * 256
            px_max_lat = n_min_y * 256
            crop_left   = px_min_lon - tx_min * 256
            crop_right  = px_max_lon - tx_min * 256
            crop_top    = px_max_lat - ty_min * 256
            crop_bottom = px_min_lat - ty_min * 256

            if crop_right > crop_left and crop_bottom > crop_top:
                cropped = stitched.crop((
                    int(crop_left), int(crop_top),
                    int(crop_right), int(crop_bottom),
                ))
                cropped = cropped.resize((w, h))
                base_bg = np.array(cropped)
                rgba[..., :3] = base_bg[..., :3]
                rgba[..., 3] = 255
                bg_loaded = True
                log.info("Satellite tile background loaded (%d tiles).", len(tile_coords))

        except Exception as exc:
            log.warning("Satellite background fetch skipped: %s", exc)

    # ── 3. Offline fallback ──────────────────────────────────────────────────
    if not bg_loaded:
        rgba[..., :3] = [30, 40, 35]
        rgba[..., 3] = 255

    # ── 4. Change category colour overlays ───────────────────────────────────
    rgba[change_map == 1] = [33, 150, 243, 235]   # Water  — blue
    rgba[change_map == 2] = [46, 204, 113, 235]   # Veg    — green
    rgba[change_map == 3] = [255, 87, 34, 235]    # Urban  — orange
    rgba[change_map == 255] = [15, 20, 28, 255]   # Nodata — near-black

    out_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, mode="RGBA").save(out_path, format="PNG")
    log.info("Change map PNG written → %s", out_path)


# ─── Scene → raster path resolver ────────────────────────────────────────────


def _find_processed_raster_paths(
    db: Session,
    scene_db_id: int,
    eo_storage_root: Path,
) -> Dict[str, str]:
    """
    Query the backend's ``processed_images`` table to find COG paths for a
    scene.  Returns {index_name: relative_path_from_eo_storage_root}.

    We query the table directly (shared DB) rather than calling the backend
    over HTTP to avoid network hops and keep provenance clean.
    """
    from sqlalchemy import text
    rows = db.execute(
        text(
            "SELECT index_name, file_path FROM processed_images "
            "WHERE scene_id = :sid AND status = 'completed' "
            "  AND file_path IS NOT NULL AND file_path <> '' "
            "ORDER BY completed_at DESC"
        ),
        {"sid": scene_db_id},
    ).fetchall()

    paths: Dict[str, str] = {}
    for row in rows:
        idx_name = row[0].upper()
        rel_path = row[1]
        full_path = eo_storage_root / rel_path
        if full_path.exists():
            # Keep only the first (most recent) completed result per index
            if idx_name not in paths:
                paths[idx_name] = rel_path
        else:
            log.warning("Processed raster listed in DB but not on disk: %s", full_path)

    return paths


def _get_scene_info(db: Session, scene_db_id: int) -> dict:
    """Fetch minimal scene metadata from the backend satellite_scenes table."""
    from sqlalchemy import text
    row = db.execute(
        text(
            "SELECT scene_id, satellite, sensor, acquisition_date, "
            "       resolution_m, crs, cloud_cover "
            "FROM satellite_scenes WHERE id = :sid"
        ),
        {"sid": scene_db_id},
    ).fetchone()
    if not row:
        raise ValueError(f"Satellite scene with DB id={scene_db_id} not found.")
    return {
        "db_id": scene_db_id,
        "scene_id": row[0],
        "satellite": row[1],
        "sensor": row[2],
        "acquisition_date": str(row[3]),
        "resolution_m": row[4],
        "crs": row[5],
        "cloud_cover": row[6],
    }


# ─── Main pipeline runner ─────────────────────────────────────────────────────

async def run_change_detection_job(job_id: str) -> None:
    """
    Async pipeline runner.  Called as an asyncio background task.

    Steps
    -----
    1. Mark job as "running".
    2. Resolve before/after processed raster paths from the shared DB.
    3. Load and align index pairs (data_loader).
    4. Run SpectralThresholdDetector (change_detection).
    5. Write change-map COG to ml_storage_path.
    6. Persist MLResult with full provenance.
    7. Mark job "completed" — or "failed" on any error.

    Future migration note
    ---------------------
    To move to a worker queue, replace the asyncio.create_task() call in the
    router with queue.enqueue(run_change_detection_job_sync, job_id).
    This function becomes a thin wrapper around a synchronous version.
    """
    # Run the blocking I/O in a thread pool to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _run_change_detection_job_sync, job_id)


def _run_change_detection_job_sync(job_id: str) -> None:
    """Synchronous implementation — safe to run in a thread executor."""
    db: Session = SessionLocal()
    try:
        _execute_pipeline(db, job_id)
    except Exception as exc:
        log.exception("Pipeline runner crashed for job %s", job_id)
        try:
            job = db.query(MLAnalysisJob).filter(MLAnalysisJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.error_message = f"Runner error: {str(exc)[:800]}"
                job.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()


def _execute_pipeline(db: Session, job_id: str) -> None:
    """Core pipeline logic — runs inside the thread executor."""

    # ── 1. Load job ────────────────────────────────────────────────────────────
    job = db.query(MLAnalysisJob).filter(MLAnalysisJob.id == job_id).first()
    if not job:
        raise ValueError(f"Job {job_id} not found in database.")

    log.info("Starting pipeline for job %s (before=%d after=%d)",
             job_id, job.before_scene_db_id, job.after_scene_db_id)

    job.status = "running"
    job.started_at = datetime.now(timezone.utc)
    db.commit()

    params = job.parameters or {}
    k_sigma = float(params.get("k_sigma", settings.k_sigma))
    min_area_px = int(params.get("min_change_area_px", settings.min_change_area_px))

    eo_root = Path(settings.eo_storage_path)
    ml_root = Path(settings.ml_storage_path)

    # ── 2. Get scene metadata ──────────────────────────────────────────────────
    before_info = _get_scene_info(db, job.before_scene_db_id)
    after_info = _get_scene_info(db, job.after_scene_db_id)

    log.info("Before scene: %s (%s)", before_info["scene_id"], before_info["acquisition_date"])
    log.info("After  scene: %s (%s)", after_info["scene_id"], after_info["acquisition_date"])

    # ── 3. Resolve processed raster paths ─────────────────────────────────────
    before_paths = _find_processed_raster_paths(db, job.before_scene_db_id, eo_root)
    after_paths = _find_processed_raster_paths(db, job.after_scene_db_id, eo_root)

    if not before_paths:
        raise ValueError(
            f"No completed Phase 5A rasters found for before-scene (DB id={job.before_scene_db_id}). "
            "Run EO index processing (NDVI/NDWI/NDBI) for this scene first."
        )
    if not after_paths:
        raise ValueError(
            f"No completed Phase 5A rasters found for after-scene (DB id={job.after_scene_db_id}). "
            "Run EO index processing (NDVI/NDWI/NDBI) for this scene first."
        )

    log.info("Before raster paths: %s", list(before_paths.keys()))
    log.info("After  raster paths: %s", list(after_paths.keys()))

    # ── 4. Load and align index pairs ─────────────────────────────────────────
    before_arrs, after_arrs, valid_mask, raster_meta, align_provenance = (
        load_multi_index_pairs(eo_root, before_paths, after_paths)
    )

    # ── 5. Run change detection ────────────────────────────────────────────────
    detector = SpectralThresholdDetector(k_sigma=k_sigma, min_change_area_px=min_area_px)
    result: ChangeResult = detector.detect(before_arrs, after_arrs, valid_mask, raster_meta)

    # ── 6. Write change map COG & PNG preview ──────────────────────────────────
    map_fname = f"change_map_{job_id}.tif"
    png_fname = f"change_map_{job_id}.png"
    out_path = ml_root / map_fname
    png_path = ml_root / png_fname

    _write_change_map_cog(result.change_map, raster_meta, out_path)
    demo_bg = eo_root / "demo" / job.location_id / "after_rgb.png"
    _write_change_map_png(result.change_map, png_path, bounds_wgs84=raster_meta.bounds_wgs84, bg_img_path=demo_bg)

    # Relative path for storage (relative to eo_root)
    try:
        rel_change_map = str(out_path.relative_to(eo_root))
    except ValueError:
        rel_change_map = str(out_path)

    # ── 7. Build full provenance ───────────────────────────────────────────────
    provenance = {
        "algorithm": {
            "name": result.algorithm_name,
            "version": result.algorithm_version,
            "type": result.algorithm_type,
            "parameters": {
                "k_sigma": k_sigma,
                "min_change_area_px": min_area_px,
            },
            "indices_used": result.extra_metadata.get("indices_used", []),
            "thresholds": result.extra_metadata.get("thresholds", {}),
        },
        "inputs": {
            "before": {
                **before_info,
                "raster_paths": before_paths,
            },
            "after": {
                **after_info,
                "raster_paths": after_paths,
            },
        },
        "alignment": align_provenance,
        "masking": {
            "nodata_threshold": NODATA_THRESHOLD,
            "valid_pixels": result.valid_pixels,
            "total_pixels": result.total_pixels,
            "valid_pixel_fraction": (
                round(result.valid_pixels / result.total_pixels, 4)
                if result.total_pixels else 0.0
            ),
        },
        "output": {
            "change_map_path": rel_change_map,
            "crs": raster_meta.crs,
            "resolution_m": raster_meta.resolution_m,
            "shape": list(raster_meta.shape),
        },
        "signal_quality_index_note": (
            "SQI = mean(|Δ|_changed) / (σ_background + ε). "
            "Measures signal-to-noise separation. "
            "NOT a model accuracy or classification confidence score."
        ),
        "processing_host": socket.gethostname(),
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }

    # ── 8. Build change_statistics dict (for easy frontend querying) ───────────
    change_statistics = {
        cat_name: {
            "pixel_count": cs.pixel_count,
            "area_km2": cs.area_km2,
            "description": cs.description,
            "label_value": cs.label_value,
        }
        for cat_name, cs in result.category_stats.items()
    }

    # ── 9. Persist MLResult ────────────────────────────────────────────────────
    ml_result = MLResult(
        job_id=job_id,
        algorithm_name=result.algorithm_name,
        algorithm_version=result.algorithm_version,
        algorithm_type=result.algorithm_type,
        change_map_path=rel_change_map,
        change_map_crs=raster_meta.crs,
        change_map_bounds=list(raster_meta.bounds_wgs84),
        total_area_km2=result.total_area_km2,
        changed_area_km2=result.changed_area_km2,
        changed_pct=result.changed_pct,
        signal_quality_index=result.signal_quality_index,
        change_statistics=change_statistics,
        provenance=provenance,
    )
    db.add(ml_result)

    # ── 10. Mark job completed ─────────────────────────────────────────────────
    job.status = "completed"
    job.completed_at = datetime.now(timezone.utc)
    db.commit()

    log.info(
        "Job %s completed. changed=%.2f%% (%.4f km²) SQI=%.3f",
        job_id, result.changed_pct, result.changed_area_km2, result.signal_quality_index,
    )
