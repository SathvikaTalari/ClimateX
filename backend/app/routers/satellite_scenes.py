from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Any
from datetime import date
import json

from ..database import get_db
from ..models.satellite import SatelliteScene
from ..models.location import Location
from ..schemas.satellite import (
    SatelliteSceneOut,
    SatelliteSceneSearchParams,
    EOSceneOut,
    SceneIngestionRequest,
    IngestionStatusOut,
    SceneFootprintOut,
)
from ..eo_gateway import get_registry, SceneSearchParams, EOScene
from ..services.ingestion import get_ingestion_service

router = APIRouter(prefix="/satellite-scenes", tags=["Satellite Scenes"])


@router.get(
    "",
    response_model=list[SatelliteSceneOut],
    summary="List stored satellite scenes",
)
def list_satellite_scenes(
    location_id: Optional[str] = Query(None, description="Filter by location ID"),
    domain_id: Optional[str] = Query(None, description="Filter by domain ID"),
    provider: Optional[str] = Query(None, description="Filter by provider name (e.g. copernicus, usgs)"),
    sensor: Optional[str] = Query(None, description="Filter by sensor name"),
    satellite: Optional[str] = Query(None, description="Filter by satellite name"),
    status: Optional[str] = Query(None, description="Filter by ingestion status (pending, processing, completed, failed)"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
):
    """
    Returns stored satellite scenes ordered by most recent acquisition date first.
    """
    query = db.query(SatelliteScene).order_by(SatelliteScene.acquisition_date.desc())

    if location_id:
        query = query.filter(SatelliteScene.location_id == location_id)
    if domain_id:
        query = query.filter(SatelliteScene.domain_id == domain_id)
    if provider:
        query = query.filter(SatelliteScene.provider.ilike(f"%{provider}%"))
    if sensor:
        query = query.filter(SatelliteScene.sensor.ilike(f"%{sensor}%"))
    if satellite:
        query = query.filter(SatelliteScene.satellite.ilike(f"%{satellite}%"))
    if status:
        query = query.filter(SatelliteScene.ingestion_status == status)

    scenes = query.offset(offset).limit(limit).all()
    return [SatelliteSceneOut.from_orm_model(s) for s in scenes]


@router.get(
    "/by-location",
    response_model=list[SatelliteSceneOut],
    summary="Get scenes for a specific coordinate point or location ID",
)
def get_scenes_by_location(
    location_id: Optional[str] = Query(None, description="Location ID (e.g. loc-1)"),
    lat: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Latitude"),
    lon: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Longitude"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Find scenes covering a given location or lat/lon coordinates.
    """
    target_lat = lat
    target_lon = lon

    if location_id:
        loc = db.query(Location).filter(Location.id == location_id).first()
        if not loc:
            raise HTTPException(status_code=404, detail=f"Location {location_id} not found")
        target_lat = loc.latitude
        target_lon = loc.longitude

    if target_lat is None or target_lon is None:
        raise HTTPException(status_code=400, detail="Must specify either location_id or lat and lon")

    # Range filter using bbox_min/max columns
    query = (
        db.query(SatelliteScene)
        .filter(
            SatelliteScene.bbox_min_lon <= target_lon,
            SatelliteScene.bbox_max_lon >= target_lon,
            SatelliteScene.bbox_min_lat <= target_lat,
            SatelliteScene.bbox_max_lat >= target_lat,
        )
        .order_by(SatelliteScene.acquisition_date.desc())
        .limit(limit)
    )

    scenes = query.all()
    # Fallback to location_id matching if bbox columns are not populated
    if not scenes and location_id:
        scenes = (
            db.query(SatelliteScene)
            .filter(SatelliteScene.location_id == location_id)
            .order_by(SatelliteScene.acquisition_date.desc())
            .limit(limit)
            .all()
        )

    return [SatelliteSceneOut.from_orm_model(s) for s in scenes]


@router.post(
    "/search",
    response_model=list[EOSceneOut],
    summary="Search satellite scenes across real EO data providers",
)
async def search_satellite_scenes(
    params: SatelliteSceneSearchParams,
    db: Session = Depends(get_db),
):
    """
    Searches connected satellite providers (Copernicus, USGS, UP42) for scenes matching criteria.
    Returns scene metadata, cloud cover, bounding box, resolution, and ingestion availability.
    """
    try:
        search_params = SceneSearchParams(
            date_from=params.date_from,
            date_to=params.date_to,
            lat=params.lat,
            lon=params.lon,
            bbox=params.bbox,
            satellite=params.satellite,
            cloud_cover_max=params.cloud_cover_max,
            limit=params.limit,
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))

    registry = get_registry()
    scenes = await registry.search_all_providers(search_params, providers=params.providers)

    # Check which scenes are already stored/ingested in DB
    existing_scenes = {
        (s.provider, s.scene_id)
        for s in db.query(SatelliteScene.provider, SatelliteScene.scene_id).all()
    }

    out_scenes: list[EOSceneOut] = []
    for scene in scenes:
        provider_inst = registry.get_provider(scene.provider)
        req_creds = False
        if provider_inst and not provider_inst.is_configured:
            req_creds = True
        elif scene.provider == "copernicus" and provider_inst and not getattr(provider_inst, "_download_configured", False):
            req_creds = True

        is_ingested = (scene.provider, scene.scene_id) in existing_scenes

        out_scenes.append(
            EOSceneOut(
                scene_id=scene.scene_id,
                provider=scene.provider,
                satellite=scene.satellite,
                sensor=scene.sensor,
                acquisition_date=scene.acquisition_date,
                cloud_cover=scene.cloud_cover,
                bbox=scene.bbox,
                footprint_geojson=scene.footprint_geojson,
                resolution_m=scene.resolution_m,
                source_url=scene.source_url,
                processing_level=scene.processing_level,
                bands=scene.bands,
                metadata=scene.metadata,
                download_requires_credentials=req_creds,
                is_already_ingested=is_ingested,
            )
        )

    return out_scenes


@router.post(
    "/ingest",
    response_model=SatelliteSceneOut,
    summary="Start scene ingestion",
)
async def ingest_scene(
    req: SceneIngestionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Ingests a selected satellite scene.
    Validates metadata, avoids duplicates, and saves PostGIS spatial footprint & provenance record.
    """
    ingestion_service = get_ingestion_service()
    registry = get_registry()

    # Convert request to canonical EOScene
    bbox = req.bbox or (0.0, 0.0, 0.0, 0.0)
    eo_scene = EOScene(
        scene_id=req.scene_id,
        provider=req.provider,
        satellite=req.satellite or "Satellite",
        sensor=req.sensor or "Sensor",
        acquisition_date=req.acquisition_date,
        cloud_cover=req.cloud_cover,
        bbox=bbox,
        footprint_geojson=req.footprint_geojson,
        resolution_m=req.resolution_m,
        source_url=req.source_url,
        bands=req.bands,
        metadata=req.metadata,
    )

    provider_inst = registry.get_provider(req.provider)

    if not req.download_raster or not provider_inst or not provider_inst.is_configured:
        # Create metadata-only record (no download)
        record = ingestion_service.metadata_only_record(
            db=db,
            scene=eo_scene,
            location_id=req.location_id,
            domain_id=req.domain_id,
        )
    else:
        # Full download and ingestion service call
        record = await ingestion_service.ingest_scene(
            db=db,
            scene=eo_scene,
            provider_instance=provider_inst,
            location_id=req.location_id,
            domain_id=req.domain_id,
        )

    return SatelliteSceneOut.from_orm_model(record)


@router.get(
    "/ingestion/{scene_identifier}/status",
    response_model=IngestionStatusOut,
    summary="Check ingestion status",
)
def get_ingestion_status(
    scene_identifier: str,
    db: Session = Depends(get_db),
):
    """
    Checks the status of scene ingestion by DB ID or scene_id string.
    """
    if scene_identifier.isdigit():
        scene = db.query(SatelliteScene).filter(SatelliteScene.id == int(scene_identifier)).first()
    else:
        scene = db.query(SatelliteScene).filter(SatelliteScene.scene_id == scene_identifier).first()

    if not scene:
        raise HTTPException(status_code=404, detail=f"Scene {scene_identifier} not found")

    return IngestionStatusOut.from_orm_model(scene)


@router.get(
    "/{scene_identifier}",
    response_model=SatelliteSceneOut,
    summary="Get scene metadata by ID",
)
def get_satellite_scene(
    scene_identifier: str,
    db: Session = Depends(get_db),
):
    """
    Retrieves full metadata for a stored satellite scene by database ID or scene_id.
    """
    if scene_identifier.isdigit():
        scene = db.query(SatelliteScene).filter(SatelliteScene.id == int(scene_identifier)).first()
    else:
        scene = db.query(SatelliteScene).filter(SatelliteScene.scene_id == scene_identifier).first()

    if not scene:
        raise HTTPException(status_code=404, detail=f"Scene {scene_identifier} not found")

    return SatelliteSceneOut.from_orm_model(scene)


@router.get(
    "/{scene_identifier}/footprint",
    response_model=SceneFootprintOut,
    summary="Get scene footprint and bounding box",
)
def get_scene_footprint(
    scene_identifier: str,
    db: Session = Depends(get_db),
):
    """
    Returns spatial boundary information (GeoJSON footprint polygon and bounding box).
    """
    if scene_identifier.isdigit():
        scene = db.query(SatelliteScene).filter(SatelliteScene.id == int(scene_identifier)).first()
    else:
        scene = db.query(SatelliteScene).filter(SatelliteScene.scene_id == scene_identifier).first()

    if not scene:
        raise HTTPException(status_code=404, detail=f"Scene {scene_identifier} not found")

    bbox = None
    if (
        scene.bbox_min_lon is not None
        and scene.bbox_min_lat is not None
        and scene.bbox_max_lon is not None
        and scene.bbox_max_lat is not None
    ):
        bbox = (scene.bbox_min_lon, scene.bbox_min_lat, scene.bbox_max_lon, scene.bbox_max_lat)

    footprint_geojson = None
    if scene.footprint is not None:
        try:
            # Convert PostGIS geometry to GeoJSON via ST_AsGeoJSON
            geojson_str = db.scalar(func.ST_AsGeoJSON(scene.footprint))
            if geojson_str:
                footprint_geojson = json.loads(geojson_str)
        except Exception:
            pass

    if not footprint_geojson and bbox:
        # Fallback to constructing GeoJSON box from bbox
        footprint_geojson = {
            "type": "Polygon",
            "coordinates": [
                [
                    [bbox[0], bbox[1]],
                    [bbox[2], bbox[1]],
                    [bbox[2], bbox[3]],
                    [bbox[0], bbox[3]],
                    [bbox[0], bbox[1]],
                ]
            ],
        }

    return SceneFootprintOut(
        id=scene.id,
        scene_id=scene.scene_id,
        provider=scene.provider or "unknown",
        satellite=scene.satellite,
        sensor=scene.sensor,
        acquisition_date=scene.acquisition_date,
        bbox=bbox,
        footprint_geojson=footprint_geojson,
    )
