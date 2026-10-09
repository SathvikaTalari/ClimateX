"""
Base abstractions for the EO (Earth Observation) data gateway.

All satellite data providers must implement AbstractEOProvider.
SceneSearchParams and EOScene are the canonical data transfer objects
shared across the entire EO pipeline.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional


# ─── Search parameters ────────────────────────────────────────────────────────

@dataclass
class SceneSearchParams:
    """Unified scene search request passed to every provider."""

    date_from: date
    date_to: date

    # Location — supply EITHER a point (lat/lon) OR a bounding box
    lat: Optional[float] = None
    lon: Optional[float] = None
    # bbox: (min_lon, min_lat, max_lon, max_lat) in WGS-84
    bbox: Optional[tuple[float, float, float, float]] = None

    # Filters
    # Provider-neutral satellite name, e.g. "Sentinel-2", "Landsat-8", "Landsat-9"
    satellite: Optional[str] = None
    cloud_cover_max: float = 100.0
    limit: int = 20

    def to_bbox(self, radius_deg: float = 0.5) -> tuple[float, float, float, float]:
        """
        Return a bounding box.  Uses self.bbox if provided; otherwise derives
        a square box around (lat, lon) with the given half-width in degrees.
        """
        if self.bbox is not None:
            return self.bbox
        if self.lat is not None and self.lon is not None:
            return (
                self.lon - radius_deg,
                self.lat - radius_deg,
                self.lon + radius_deg,
                self.lat + radius_deg,
            )
        raise ValueError(
            "SceneSearchParams must have either bbox or (lat, lon) set."
        )


# ─── Scene result ─────────────────────────────────────────────────────────────

@dataclass
class EOScene:
    """
    Canonical representation of one satellite scene returned by any provider.

    footprint_geojson must be a valid GeoJSON Polygon (or None).
    bbox is (min_lon, min_lat, max_lon, max_lat).
    """

    scene_id: str                                     # Provider-native scene identifier
    provider: str                                     # "copernicus" | "usgs" | "up42"
    satellite: str                                    # e.g. "Sentinel-2A"
    sensor: str                                       # e.g. "MSI", "OLI-TIRS"
    acquisition_date: date
    cloud_cover: Optional[float]                      # 0–100 %
    bbox: tuple[float, float, float, float]           # (min_lon, min_lat, max_lon, max_lat)
    footprint_geojson: Optional[dict] = None          # GeoJSON Polygon
    resolution_m: Optional[float] = None              # Ground sample distance in metres
    source_url: Optional[str] = None                  # Download/preview URL from provider
    thumbnail_url: Optional[str] = None               # Public thumbnail optical image URL
    processing_level: Optional[str] = None           # e.g. "L2A", "L1C", "L2"
    bands: list[str] = field(default_factory=list)   # Available band names
    metadata: dict = field(default_factory=dict)     # Provider-specific extras

    @property
    def provenance(self) -> dict:
        """Full provenance record stored in the DB alongside every scene."""
        return {
            "provider": self.provider,
            "satellite": self.satellite,
            "sensor": self.sensor,
            "scene_id": self.scene_id,
            "acquisition_date": self.acquisition_date.isoformat(),
            "processing_level": self.processing_level,
            "source_url": self.source_url,
            "thumbnail_url": self.thumbnail_url,
            "cloud_cover": self.cloud_cover,
            "resolution_m": self.resolution_m,
            "bands": self.bands,
            "provider_metadata": self.metadata,
        }


# ─── Provider errors ─────────────────────────────────────────────────────────

class EOProviderError(RuntimeError):
    """Raised when a provider search or download fails non-transiently."""


class EOProviderUnconfiguredError(EOProviderError):
    """Raised when a provider is called but missing required credentials."""


class EOProviderDownloadError(EOProviderError):
    """Raised when a provider download fails."""


# ─── Abstract provider interface ─────────────────────────────────────────────

class AbstractEOProvider(abc.ABC):
    """
    Interface that every satellite data provider adapter must implement.

    Providers are responsible for:
      - Translating SceneSearchParams into provider-specific API calls
      - Returning a list of EOScene results
      - Downloading a single scene to a local Path
    """

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        """Short identifier used in DB records, e.g. 'copernicus'."""

    @property
    @abc.abstractmethod
    def supported_satellites(self) -> list[str]:
        """
        List of satellite names this provider can serve.
        Used by the registry to route searches efficiently.
        """

    @property
    @abc.abstractmethod
    def is_configured(self) -> bool:
        """
        Returns True if the provider has the credentials / config it needs.
        If False, the provider will NOT be included in multi-provider searches.
        Note: Copernicus search-only mode is considered configured even without
        download credentials (is_configured=True, but download raises an error).
        """

    @property
    def supports_search_without_credentials(self) -> bool:
        """
        If True, the provider can search even without download credentials.
        Defaults to False; override in providers that have a public search API.
        """
        return False

    @abc.abstractmethod
    async def search(self, params: SceneSearchParams) -> list[EOScene]:
        """
        Search for satellite scenes matching the given parameters.
        Returns an empty list (not an error) if no scenes are found.
        May raise EOProviderError on API failure.
        """

    @abc.abstractmethod
    async def download(self, scene: EOScene, dest_path: Path) -> Path:
        """
        Download the scene raster to dest_path directory.
        Returns the Path of the downloaded file.
        Raises EOProviderDownloadError on failure.
        Raises EOProviderUnconfiguredError if download credentials are missing.
        """
