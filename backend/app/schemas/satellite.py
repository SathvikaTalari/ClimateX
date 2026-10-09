from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, Any


# ─── Search Request / Response Schemas ───────────────────────────────────────

class SatelliteSceneSearchParams(BaseModel):
    date_from: date
    date_to: date
    lat: Optional[float] = Field(None, ge=-90.0, le=90.0)
    lon: Optional[float] = Field(None, ge=-180.0, le=180.0)
    bbox: Optional[tuple[float, float, float, float]] = None  # (min_lon, min_lat, max_lon, max_lat)
    satellite: Optional[str] = None  # e.g., "Sentinel-2", "Landsat-8"
    cloud_cover_max: float = Field(100.0, ge=0.0, le=100.0)
    providers: Optional[list[str]] = None  # e.g. ["copernicus", "usgs"]
    limit: int = Field(20, ge=1, le=100)


class EOSceneOut(BaseModel):
    """Provider scene returned during live provider search."""
    scene_id: str
    provider: str
    satellite: str
    sensor: str
    acquisition_date: date
    cloud_cover: Optional[float] = None
    bbox: tuple[float, float, float, float]
    footprint_geojson: Optional[dict[str, Any]] = None
    resolution_m: Optional[float] = None
    source_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    processing_level: Optional[str] = None
    bands: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    download_requires_credentials: bool = False
    is_already_ingested: bool = False


# ─── Ingestion Request / Status Schemas ──────────────────────────────────────

class SceneIngestionRequest(BaseModel):
    scene_id: str
    provider: str = "copernicus"
    satellite: Optional[str] = None
    sensor: Optional[str] = None
    acquisition_date: date
    cloud_cover: Optional[float] = None
    resolution_m: Optional[float] = None
    bbox: Optional[tuple[float, float, float, float]] = None
    footprint_geojson: Optional[dict[str, Any]] = None
    source_url: Optional[str] = None
    bands: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    location_id: Optional[str] = None
    domain_id: Optional[str] = None
    download_raster: bool = True  # If False, stores metadata-only scene record


class IngestionStatusOut(BaseModel):
    id: int
    scene_id: str
    provider: str
    ingestion_status: str  # "pending" | "processing" | "completed" | "failed"
    ingestion_error: Optional[str] = None
    ingested_at: Optional[datetime] = None
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_model(cls, scene) -> "IngestionStatusOut":
        return cls(
            id=scene.id,
            scene_id=scene.scene_id,
            provider=scene.provider or "unknown",
            ingestion_status=scene.ingestion_status or "completed",
            ingestion_error=scene.ingestion_error,
            ingested_at=scene.ingested_at,
            file_path=scene.file_path,
            file_size_bytes=scene.file_size_bytes,
        )


# ─── DB Scene Out Schema ──────────────────────────────────────────────────────

class SatelliteSceneOut(BaseModel):
    id: int
    scene_id: str
    provider: str = "unknown"
    satellite: Optional[str] = None
    sensor: str
    acquisition_date: date
    cloud_cover: Optional[float] = None
    resolution_m: Optional[float] = None
    bbox: Optional[tuple[float, float, float, float]] = None
    source_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    crs: Optional[str] = None
    bands: Optional[list[str]] = Field(default_factory=list)
    provenance: Optional[dict[str, Any]] = Field(default_factory=dict)
    ingestion_status: str = "completed"
    ingestion_error: Optional[str] = None
    ingested_at: Optional[datetime] = None
    scene_metadata: Optional[dict[str, Any]] = Field(default_factory=dict)
    location_id: Optional[str] = None
    domain_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_model(cls, scene) -> "SatelliteSceneOut":
        bbox = None
        if (
            scene.bbox_min_lon is not None
            and scene.bbox_min_lat is not None
            and scene.bbox_max_lon is not None
            and scene.bbox_max_lat is not None
        ):
            bbox = (scene.bbox_min_lon, scene.bbox_min_lat, scene.bbox_max_lon, scene.bbox_max_lat)

        provenance_dict = scene.provenance or {}
        return cls(
            id=scene.id,
            scene_id=scene.scene_id,
            provider=scene.provider or "unknown",
            satellite=scene.satellite,
            sensor=scene.sensor,
            acquisition_date=scene.acquisition_date,
            cloud_cover=scene.cloud_cover,
            resolution_m=scene.resolution_m,
            bbox=bbox,
            source_url=scene.source_url,
            thumbnail_url=provenance_dict.get("thumbnail_url"),
            file_path=scene.file_path,
            file_size_bytes=scene.file_size_bytes,
            crs=scene.crs,
            bands=scene.bands or [],
            provenance=provenance_dict,
            ingestion_status=scene.ingestion_status or "completed",
            ingestion_error=scene.ingestion_error,
            ingested_at=scene.ingested_at,
            scene_metadata=scene.scene_metadata or {},
            location_id=scene.location_id,
            domain_id=scene.domain_id,
            created_at=scene.created_at,
        )


class SceneFootprintOut(BaseModel):
    id: int
    scene_id: str
    provider: str
    satellite: Optional[str] = None
    sensor: str
    acquisition_date: date
    bbox: Optional[tuple[float, float, float, float]] = None
    footprint_geojson: Optional[dict[str, Any]] = None
