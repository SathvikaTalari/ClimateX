"""
EO Processing Router — Phase 5A
Endpoints:
  POST /satellite-scenes/{id}/process             — Run index (NDVI/NDWI/NDBI/LST)
  GET  /satellite-scenes/{id}/processing-status   — All processed records for a scene
  GET  /satellite-scenes/{id}/processed-outputs   — Only completed records
  GET  /satellite-scenes/{id}/composite           — Stream RGB / False-Color / SWIR PNG
  GET  /processed-images/{id}/file               — Download COG GeoTIFF
  GET  /processed-images/{id}/histogram          — Return 32-bin pixel histogram
  GET  /locations/{id}/spatial-features          — Zonal statistics for a location
  GET  /locations/{id}/spatial-features/export   — Download GeoJSON or CSV export
"""
import logging
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)

from ..database import get_db
from ..models.satellite import SatelliteScene
from ..models.location import Location
from ..models.processing import ProcessedImage, SpatialFeature
from ..schemas.processing import (
    ProcessingRequest, ProcessedImageOut, SpatialFeatureOut,
    HistogramOut, CompositeRequest,
)
from ..services.eo_processor import get_eo_processor
from ..config import get_settings

router = APIRouter(prefix="", tags=["EO Processing"])
settings = get_settings()


# ─── Scene lookup helper ──────────────────────────────────────────────────────

def _get_scene(db: Session, scene_identifier: str) -> SatelliteScene:
    if scene_identifier.isdigit():
        scene = db.query(SatelliteScene).filter(SatelliteScene.id == int(scene_identifier)).first()
    else:
        scene = db.query(SatelliteScene).filter(SatelliteScene.scene_id == scene_identifier).first()
    if not scene:
        raise HTTPException(status_code=404, detail=f"Satellite scene '{scene_identifier}' not found.")
    return scene


# ─── Feature 1/2: Index Processing ───────────────────────────────────────────

@router.post(
    "/satellite-scenes/{scene_identifier}/process",
    response_model=ProcessedImageOut,
    summary="Compute an environmental index (NDVI / NDWI / NDBI / LST) for a satellite scene",
)
def process_satellite_scene(
    scene_identifier: str,
    req: ProcessingRequest,
    db: Session = Depends(get_db),
):
    scene = _get_scene(db, scene_identifier)

    if scene.ingestion_status != "completed" or not scene.file_path:
        raise HTTPException(
            status_code=400,
            detail=f"Scene '{scene.scene_id}' is not fully ingested or raster data is unavailable.",
        )

    # Resolve location
    location = None
    if req.location_id:
        location = db.query(Location).filter(Location.id == req.location_id).first()
        if not location:
            raise HTTPException(status_code=404, detail=f"Location '{req.location_id}' not found.")
    elif scene.location_id:
        location = db.query(Location).filter(Location.id == scene.location_id).first()

    index_name = req.index_name.upper()

    # Get or create processing record
    processed_rec = (
        db.query(ProcessedImage)
        .filter(ProcessedImage.scene_id == scene.id, ProcessedImage.index_name == index_name)
        .first()
    )

    if processed_rec and processed_rec.status == "completed":
        return ProcessedImageOut.from_orm_model(processed_rec)

    if not processed_rec:
        processed_rec = ProcessedImage(
            scene_id=scene.id,
            index_name=index_name,
            file_path="",
            status="processing",
        )
        db.add(processed_rec)
    else:
        processed_rec.status = "processing"
        processed_rec.error_message = None

    try:
        db.commit()
        db.refresh(processed_rec)
    except Exception:
        db.rollback()

    processor = get_eo_processor()
    try:
        rel_path, stats = processor.process_index(scene, index_name, location)

        processed_rec.file_path    = str(rel_path)
        processed_rec.status       = "completed"
        processed_rec.completed_at = datetime.now(timezone.utc)
        processed_rec.resolution_m = scene.resolution_m
        processed_rec.crs          = scene.crs
        processed_rec.bounds       = (
            [scene.bbox_min_lon, scene.bbox_min_lat, scene.bbox_max_lon, scene.bbox_max_lat]
            if scene.bbox_min_lon is not None else None
        )
        db.commit()

        # Persist spatial feature (zonal stats)
        if location:
            try:
                db.query(SpatialFeature).filter(
                    SpatialFeature.location_id == location.id,
                    SpatialFeature.index_name == index_name,
                ).delete(synchronize_session=False)

                feat = SpatialFeature(
                    location_id=location.id,
                    processed_image_id=processed_rec.id,
                    index_name=index_name,
                    mean_value=stats.get("mean_value"),
                    min_value=stats.get("min_value"),
                    max_value=stats.get("max_value"),
                    std_dev=stats.get("std_dev"),
                    valid_pixels=stats.get("valid_pixels"),
                )
                db.add(feat)
                db.commit()
            except Exception as feat_err:
                log.warning("Could not store spatial feature: %s", feat_err)
                db.rollback()

        return ProcessedImageOut.from_orm_model(processed_rec)

    except Exception as exc:
        log.exception("Error processing scene %s index %s", scene_identifier, index_name)
        db.rollback()
        try:
            processed_rec.status = "failed"
            processed_rec.error_message = str(exc)[:1000]
            db.commit()
        except Exception:
            db.rollback()
        raise HTTPException(status_code=400, detail=f"Processing failed: {exc}")


# ─── Processing Status & Outputs ──────────────────────────────────────────────

@router.get(
    "/satellite-scenes/{scene_identifier}/processing-status",
    response_model=List[ProcessedImageOut],
    summary="Get processing status for all indices of a satellite scene",
)
def get_processing_status(scene_identifier: str, db: Session = Depends(get_db)):
    scene = _get_scene(db, scene_identifier)
    processed = db.query(ProcessedImage).filter(ProcessedImage.scene_id == scene.id).all()
    return [ProcessedImageOut.from_orm_model(p) for p in processed]


@router.get(
    "/satellite-scenes/{scene_identifier}/processed-outputs",
    response_model=List[ProcessedImageOut],
    summary="Get completed processed outputs for a scene",
)
def get_processed_outputs(scene_identifier: str, db: Session = Depends(get_db)):
    scene = _get_scene(db, scene_identifier)
    processed = (
        db.query(ProcessedImage)
        .filter(ProcessedImage.scene_id == scene.id, ProcessedImage.status == "completed")
        .all()
    )
    return [ProcessedImageOut.from_orm_model(p) for p in processed]


# ─── Feature 1: RGB / False-Color Composite Generator ─────────────────────────

@router.get(
    "/satellite-scenes/{scene_identifier}/composite",
    summary="Generate and stream a RGB or False-Color PNG composite image",
)
def get_scene_composite(
    scene_identifier: str,
    mode: str = Query("RGB", description="Composite mode: RGB | FALSE_COLOR | SWIR"),
    location_id: Optional[str] = Query(None, description="Optional location ID to clip the composite"),
    db: Session = Depends(get_db),
):
    """
    Renders a PNG composite image from the raw satellite raster bands.
    - **RGB**: Natural Color (Red-Green-Blue) — shows terrain, vegetation, water as true colour.
    - **FALSE_COLOR**: Vegetation Infrared (NIR-Red-Green) — dense vegetation appears bright red.
    - **SWIR**: Burn Scar / Urban (SWIR-NIR-Red) — highlights built-up land, fire scars, bare soil.
    """
    scene = _get_scene(db, scene_identifier)

    if not scene.file_path:
        raise HTTPException(status_code=400, detail="Scene has no raster file. Select a [Raster Ready] scene.")

    location = None
    if location_id:
        location = db.query(Location).filter(Location.id == location_id).first()
    elif scene.location_id:
        location = db.query(Location).filter(Location.id == scene.location_id).first()

    processor = get_eo_processor()
    try:
        png_path = processor.generate_composite(scene, mode=mode, location=location)
    except Exception as exc:
        log.exception("Composite generation failed for scene %s mode %s", scene_identifier, mode)
        raise HTTPException(status_code=500, detail=f"Composite generation failed: {exc}")

    if not png_path.exists():
        raise HTTPException(status_code=500, detail="Generated PNG not found on disk.")

    return FileResponse(
        path=str(png_path),
        media_type="image/png",
        filename=png_path.name,
        headers={"Cache-Control": "public, max-age=3600"},
    )


# ─── COG File Download ────────────────────────────────────────────────────────

@router.get(
    "/processed-images/{image_id}/file",
    summary="Download a processed COG GeoTIFF file",
)
def get_processed_image_file(image_id: int, db: Session = Depends(get_db)):
    processed = db.query(ProcessedImage).filter(ProcessedImage.id == image_id).first()
    if not processed or not processed.file_path:
        raise HTTPException(status_code=404, detail="Processed image not found.")

    full_path = Path(settings.eo_storage_path) / processed.file_path
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File missing from storage.")

    return FileResponse(path=str(full_path), media_type="image/tiff", filename=full_path.name)


# ─── Feature 3: Pixel Value Histogram ────────────────────────────────────────

@router.get(
    "/processed-images/{image_id}/histogram",
    response_model=HistogramOut,
    summary="Compute 32-bin pixel value distribution histogram for a processed raster",
)
def get_processed_image_histogram(
    image_id: int,
    n_bins: int = Query(32, ge=8, le=128, description="Number of histogram bins"),
    db: Session = Depends(get_db),
):
    """
    Reads the processed COG raster and returns a statistical histogram of valid pixel values.
    Useful for understanding the spectral distribution and spotting anomalies.
    """
    processed = db.query(ProcessedImage).filter(ProcessedImage.id == image_id).first()
    if not processed:
        raise HTTPException(status_code=404, detail="Processed image not found.")
    if processed.status != "completed":
        raise HTTPException(status_code=400, detail=f"Processing is not complete (status: {processed.status}).")

    full_path = Path(settings.eo_storage_path) / processed.file_path
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Raster file missing from storage.")

    processor = get_eo_processor()
    try:
        result = processor.compute_histogram(full_path, processed.index_name, n_bins=n_bins)
    except Exception as exc:
        log.exception("Histogram computation failed for image %d", image_id)
        raise HTTPException(status_code=500, detail=f"Histogram failed: {exc}")

    return HistogramOut(**result.to_dict())


# ─── Zonal Statistics ─────────────────────────────────────────────────────────

@router.get(
    "/locations/{location_id}/spatial-features",
    response_model=List[SpatialFeatureOut],
    summary="Get calculated environmental index statistics for a location",
)
def get_location_spatial_features(
    location_id: str,
    index_name: Optional[str] = Query(None, description="Filter by index name, e.g. NDVI"),
    db: Session = Depends(get_db),
):
    query = db.query(SpatialFeature).filter(SpatialFeature.location_id == location_id)
    if index_name:
        query = query.filter(SpatialFeature.index_name == index_name.upper())
    features = query.order_by(SpatialFeature.created_at.desc()).all()
    return [SpatialFeatureOut.from_orm_model(f) for f in features]


# ─── Feature 4: Spatial Feature Export (GeoJSON / CSV) ───────────────────────

@router.get(
    "/locations/{location_id}/spatial-features/export",
    summary="Export spatial statistics in GeoJSON or CSV format",
)
def export_spatial_features(
    location_id: str,
    format: str = Query("geojson", description="Export format: geojson | csv"),
    index_name: Optional[str] = Query(None, description="Filter by index name, e.g. NDVI"),
    db: Session = Depends(get_db),
):
    """
    Download zonal statistics as a GeoJSON FeatureCollection or CSV file.
    Useful for GIS analysis in QGIS, ArcGIS, or Python/R data pipelines.
    """
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail=f"Location '{location_id}' not found.")

    query = db.query(SpatialFeature).filter(SpatialFeature.location_id == location_id)
    if index_name:
        query = query.filter(SpatialFeature.index_name == index_name.upper())
    features = query.order_by(SpatialFeature.created_at.desc()).all()

    if not features:
        raise HTTPException(
            status_code=404,
            detail=f"No spatial features found for location '{location_id}'. Run index processing first."
        )

    processor = get_eo_processor()
    fmt = format.lower()

    if fmt == "csv":
        csv_content = processor.export_spatial_features_csv(features)
        filename = f"climatex_features_{location_id}.csv"
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    elif fmt == "geojson":
        geojson = processor.export_spatial_features_geojson(features, location)
        filename = f"climatex_features_{location_id}.geojson"
        return StreamingResponse(
            iter([json.dumps(geojson, indent=2)]),
            media_type="application/geo+json",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format '{format}'. Use: geojson | csv")
