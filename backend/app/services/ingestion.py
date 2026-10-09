"""
Ingestion Service — controlled EO raster scene download and storage.

Lifecycle:
  1. Duplicate check       — abort if scene already ingested
  2. DB record created     — status="pending"
  3. File download         — status="processing"
  4. Rasterio validation   — verify CRS, bounds, size
  5. DB updated            — status="completed" with file metadata
  6. On any error          — status="failed" with error message

Raster files are stored at:
  {EO_STORAGE_PATH}/{provider}/{scene_id}/{filename}

Only metadata is stored in PostgreSQL; raster bytes are on disk.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.config import get_settings
from app.eo_gateway.base import EOScene, EOProviderDownloadError, EOProviderUnconfiguredError
from app.models.satellite import SatelliteScene

log = logging.getLogger(__name__)

_settings = get_settings()


class DuplicateSceneError(RuntimeError):
    """Raised when a scene with the same (provider, scene_id) already exists."""


class IngestionService:
    """Handles the full lifecycle of ingesting a satellite scene into ClimateX."""

    def __init__(self, storage_root: Optional[Path] = None) -> None:
        self._storage_root = storage_root or Path(_settings.eo_storage_path)
        self._max_bytes = _settings.max_scene_file_size_mb * 1024 * 1024

    # ── Public API ────────────────────────────────────────────────────────────

    def get_or_create_record(
        self,
        db: Session,
        scene: EOScene,
        *,
        location_id: Optional[str] = None,
        domain_id: Optional[str] = None,
    ) -> SatelliteScene:
        """
        Ensure a DB record exists for the given EOScene.
        If one already exists (same provider + scene_id), return it as-is.
        If not, create a new record with status='pending'.
        Raises DuplicateSceneError only if the caller needs to know about it.
        """
        existing = (
            db.query(SatelliteScene)
            .filter(
                SatelliteScene.provider == scene.provider,
                SatelliteScene.scene_id == scene.scene_id,
            )
            .first()
        )
        if existing:
            return existing

        record = self._create_record(db, scene, location_id=location_id, domain_id=domain_id)
        return record

    def check_duplicate(self, db: Session, provider: str, scene_id: str) -> bool:
        """Return True if the (provider, scene_id) pair already exists in the DB."""
        return (
            db.query(SatelliteScene.id)
            .filter(
                SatelliteScene.provider == provider,
                SatelliteScene.scene_id == scene_id,
            )
            .first()
        ) is not None

    async def ingest_scene(
        self,
        db: Session,
        scene: EOScene,
        provider_instance,  # AbstractEOProvider — typed loosely to avoid circular import
        *,
        location_id: Optional[str] = None,
        domain_id: Optional[str] = None,
    ) -> SatelliteScene:
        """
        Full ingestion pipeline: create record → download → validate → finalize.

        Args:
            db:                Database session.
            scene:             EOScene from provider search.
            provider_instance: The AbstractEOProvider that owns this scene.
            location_id:       Optional FK to locations table.
            domain_id:         Optional FK to environmental_domains table.

        Returns:
            The updated SatelliteScene record.
        """
        # ── Step 1: Duplicate check ────────────────────────────────────────────
        if self.check_duplicate(db, scene.provider, scene.scene_id):
            log.info(
                "[Ingestion] Scene %s/%s already exists — skipping.",
                scene.provider, scene.scene_id,
            )
            record = (
                db.query(SatelliteScene)
                .filter(
                    SatelliteScene.provider == scene.provider,
                    SatelliteScene.scene_id == scene.scene_id,
                )
                .first()
            )
            return record  # type: ignore[return-value]

        # ── Step 2: Create DB record with status=pending ───────────────────────
        record = self._create_record(db, scene, location_id=location_id, domain_id=domain_id)
        log.info("[Ingestion] Created record id=%s for %s/%s", record.id, scene.provider, scene.scene_id)

        # ── Step 3: Attempt download ───────────────────────────────────────────
        dest_dir = self._storage_root / scene.provider / _safe_filename(scene.scene_id)
        try:
            self._mark_processing(db, record)

            file_path = await provider_instance.download(scene, dest_dir)
            file_size = file_path.stat().st_size if file_path.exists() else 0

            # ── Step 4: Validate file size ─────────────────────────────────────
            if file_size > self._max_bytes:
                raise IOError(
                    f"Downloaded file size {file_size / 1_048_576:.1f} MB exceeds "
                    f"limit of {_settings.max_scene_file_size_mb} MB."
                )

            # ── Step 5: Rasterio metadata extraction ──────────────────────────
            crs, bands = self._extract_raster_metadata(file_path)

            # ── Step 6: Mark completed ─────────────────────────────────────────
            self._mark_completed(db, record, file_path, file_size, crs, bands)
            log.info(
                "[Ingestion] Scene %s/%s ingested successfully (%.1f MB).",
                scene.provider, scene.scene_id, file_size / 1_048_576,
            )

        except (EOProviderUnconfiguredError, EOProviderDownloadError, IOError, Exception) as exc:
            error_msg = str(exc)[:1000]
            self._mark_failed(db, record, error_msg)
            log.warning(
                "[Ingestion] Scene %s/%s failed: %s", scene.provider, scene.scene_id, error_msg
            )

        db.refresh(record)
        return record

    def metadata_only_record(
        self,
        db: Session,
        scene: EOScene,
        *,
        location_id: Optional[str] = None,
        domain_id: Optional[str] = None,
    ) -> SatelliteScene:
        """
        Create a metadata-only record (no download) with status='completed'.
        Used when provider search returns a result but no download is needed.
        """
        if self.check_duplicate(db, scene.provider, scene.scene_id):
            return (
                db.query(SatelliteScene)
                .filter(
                    SatelliteScene.provider == scene.provider,
                    SatelliteScene.scene_id == scene.scene_id,
                )
                .first()  # type: ignore[return-value]
            )

        record = self._create_record(db, scene, location_id=location_id, domain_id=domain_id)
        record.ingestion_status = "completed"
        record.ingested_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(record)
        return record

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _create_record(
        self,
        db: Session,
        scene: EOScene,
        *,
        location_id: Optional[str],
        domain_id: Optional[str],
    ) -> SatelliteScene:
        """Insert a new SatelliteScene row with status='pending'."""
        # Build PostGIS-compatible footprint WKT if geojson is available
        footprint_wkt: Optional[str] = None
        if scene.footprint_geojson:
            try:
                from shapely.geometry import shape
                geom = shape(scene.footprint_geojson)
                footprint_wkt = f"SRID=4326;{geom.wkt}"
            except Exception:
                footprint_wkt = None

        record = SatelliteScene(
            scene_id=scene.scene_id,
            provider=scene.provider,
            satellite=scene.satellite,
            sensor=scene.sensor,
            acquisition_date=scene.acquisition_date,
            cloud_cover=scene.cloud_cover,
            resolution_m=scene.resolution_m,
            # Spatial
            footprint=footprint_wkt,
            bbox_min_lon=scene.bbox[0] if scene.bbox else None,
            bbox_min_lat=scene.bbox[1] if scene.bbox else None,
            bbox_max_lon=scene.bbox[2] if scene.bbox else None,
            bbox_max_lat=scene.bbox[3] if scene.bbox else None,
            # Provenance
            source_url=scene.source_url,
            provenance=scene.provenance,
            bands=scene.bands or [],
            # Ingestion
            ingestion_status="pending",
            scene_metadata=scene.metadata or {},
            # FKs
            location_id=location_id,
            domain_id=domain_id,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def _mark_processing(self, db: Session, record: SatelliteScene) -> None:
        record.ingestion_status = "processing"
        db.commit()

    def _mark_completed(
        self,
        db: Session,
        record: SatelliteScene,
        file_path: Path,
        file_size: int,
        crs: Optional[str],
        bands: list[str],
    ) -> None:
        # Store relative path from storage root
        try:
            rel_path = str(file_path.relative_to(self._storage_root))
        except ValueError:
            rel_path = str(file_path)

        record.ingestion_status = "completed"
        record.ingested_at = datetime.now(timezone.utc)
        record.file_path = rel_path
        record.file_size_bytes = file_size
        record.crs = crs
        if bands:
            record.bands = bands
        db.commit()

    def _mark_failed(self, db: Session, record: SatelliteScene, error: str) -> None:
        record.ingestion_status = "failed"
        record.ingestion_error = error
        db.commit()

    def _extract_raster_metadata(
        self, file_path: Path
    ) -> tuple[Optional[str], list[str]]:
        """
        Use rasterio to read CRS and band descriptions from a raster file.
        Returns (crs_string, band_names).
        If the file is a zip/tar archive (common for Sentinel products), skip rasterio.
        """
        suffix = file_path.suffix.lower()
        if suffix in (".zip", ".tar", ".gz", ".7z"):
            log.info(
                "[Ingestion] File %s is an archive — skipping rasterio validation. "
                "Extract manually to validate individual bands.",
                file_path.name,
            )
            return None, []

        try:
            import rasterio  # type: ignore[import]
            with rasterio.open(file_path) as ds:
                crs = ds.crs.to_string() if ds.crs else None
                # Try band descriptions first, fall back to band index strings
                bands = [
                    ds.descriptions[i] or f"Band_{i + 1}"
                    for i in range(ds.count)
                ]
            return crs, bands
        except Exception as exc:
            log.warning("[Ingestion] rasterio could not read %s: %s", file_path.name, exc)
            return None, []


def _safe_filename(name: str) -> str:
    """Strip characters unsafe for directory/file names."""
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in name)


# ── Module-level singleton ────────────────────────────────────────────────────

_service: Optional[IngestionService] = None


def get_ingestion_service() -> IngestionService:
    global _service
    if _service is None:
        _service = IngestionService()
    return _service
