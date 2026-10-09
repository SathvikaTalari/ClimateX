"""
SatelliteScene ORM model — Phase 4 extended with EO pipeline fields.

New columns (Phase 4):
  provider, satellite, resolution_m            — scene identity
  bbox_min_lon/lat, bbox_max_lon/lat           — fast spatial coverage filter
  source_url                                   — provider download reference
  ingestion_status                             — lifecycle state machine
  ingestion_error                              — failure reason
  ingested_at                                  — when download completed
  file_path                                    — relative path to raster on disk
  file_size_bytes                              — downloaded file size
  crs                                          — coordinate reference system
  bands                                        — list of available band names
  provenance                                   — full audit JSONB
"""

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Text, ForeignKey, Date, Index, BigInteger,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from ..database import Base


class SatelliteScene(Base):
    """Represents a satellite image acquisition scene (swath/pass)."""
    __tablename__ = "satellite_scenes"

    id = Column(Integer, primary_key=True, index=True)

    # ── Core scene identity ────────────────────────────────────────────────────
    # Provider-native scene identifier (e.g. 'S2A_MSIL2A_20260814T...' or LC08_...)
    scene_id = Column(String(256), unique=True, nullable=False, index=True)
    # Provider name: "copernicus" | "usgs" | "up42"
    provider = Column(String(64), nullable=False, default="unknown", index=True)
    # Satellite name e.g. "Sentinel-2A", "Landsat-8"
    satellite = Column(String(128), nullable=True, index=True)
    # Sensor / instrument e.g. "MSI", "OLI-TIRS", "SAR-C"
    sensor = Column(String(128), nullable=False, index=True)
    acquisition_date = Column(Date, nullable=False, index=True)
    cloud_cover = Column(Float, nullable=True)            # 0.0 – 100.0 %
    resolution_m = Column(Float, nullable=True)           # Ground sample distance in metres

    # ── Spatial coverage ──────────────────────────────────────────────────────
    # PostGIS footprint polygon (scene boundary) stored in EPSG:4326
    footprint = Column(Geometry("POLYGON", srid=4326), nullable=True)
    # Denormalized bounding-box columns for fast range queries without PostGIS
    bbox_min_lon = Column(Float, nullable=True)
    bbox_min_lat = Column(Float, nullable=True)
    bbox_max_lon = Column(Float, nullable=True)
    bbox_max_lat = Column(Float, nullable=True)

    # ── Raster file storage ────────────────────────────────────────────────────
    # Relative path from EO_STORAGE_PATH root (e.g. "copernicus/S2A_.../file.zip")
    file_path = Column(Text, nullable=True)
    file_size_bytes = Column(BigInteger, nullable=True)
    crs = Column(String(64), nullable=True)               # e.g. "EPSG:4326", "EPSG:32643"
    bands = Column(JSONB, nullable=True, default=list)    # ["B02","B03","B04",...]

    # ── Provenance & source ───────────────────────────────────────────────────
    # Original provider download URL / reference
    source_url = Column(Text, nullable=True)
    # Full provenance audit record (provider, dataset, scene_id, acq_time, source_url, etc.)
    provenance = Column(JSONB, nullable=True, default=dict)

    # ── Ingestion lifecycle ───────────────────────────────────────────────────
    # State machine: "pending" → "processing" → "completed" | "failed"
    ingestion_status = Column(String(16), nullable=False, default="pending", index=True)
    ingestion_error = Column(Text, nullable=True)         # Error message if failed
    ingested_at = Column(DateTime(timezone=True), nullable=True)  # Completion timestamp

    # ── Extensible metadata bag ───────────────────────────────────────────────
    scene_metadata = Column(JSONB, nullable=True, default=dict)

    # ── Foreign keys ─────────────────────────────────────────────────────────
    location_id = Column(
        String(32), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    domain_id = Column(
        String(64), ForeignKey("environmental_domains.id", ondelete="SET NULL"), nullable=True, index=True
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_satellite_scenes_footprint", "footprint", postgresql_using="gist"),
        Index("ix_satellite_scenes_provider_scene_id", "provider", "scene_id"),
        Index("ix_satellite_scenes_acq_date", "acquisition_date"),
    )

    # ── Relationships ────────────────────────────────────────────────────────
    location = relationship("Location", back_populates="satellite_scenes")
    domain = relationship("EnvironmentalDomain", back_populates="satellite_scenes")
    observations = relationship("Observation", back_populates="scene")

    def __repr__(self) -> str:
        return (
            f"<SatelliteScene id={self.id} scene_id={self.scene_id!r} "
            f"provider={self.provider!r} status={self.ingestion_status!r}>"
        )
