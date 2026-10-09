"""
Copernicus Data Space adapter — Sentinel-1 GRD & Sentinel-2 L2A.

Search API:  https://catalogue.dataspace.copernicus.eu/stac/search (public, no auth)
Download:    Requires OAuth2 client credentials (client_id + client_secret)

Sentinel-2 L2A scenes reach ~110 km × 110 km tiles in the MGRS grid.
Sentinel-1 GRD IW scenes cover ~250 km swaths.

Reference:
  https://documentation.dataspace.copernicus.eu/APIs/STAC.html
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date
from pathlib import Path
from typing import Any

import httpx

from .base import (
    AbstractEOProvider,
    EOProviderDownloadError,
    EOProviderUnconfiguredError,
    EOScene,
    SceneSearchParams,
)

log = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────

STAC_SEARCH_URL = "https://catalogue.dataspace.copernicus.eu/stac/search"
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

# STAC collection names for each satellite family (lowercase preferred by Copernicus STAC API)
_COLLECTIONS: dict[str, str] = {
    "Sentinel-1": "sentinel-1-grd",
    "Sentinel-2": "sentinel-2-l2a",
}

# Sentinel-2 bands (L2A)
_S2_BANDS = ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B09", "B11", "B12", "SCL"]
# Sentinel-1 GRD typical polarisations
_S1_BANDS = ["VV", "VH"]


# ─── Provider ────────────────────────────────────────────────────────────────

class CopernicusProvider(AbstractEOProvider):
    """
    Fetches Sentinel-1 and Sentinel-2 scenes from the Copernicus Data Space.
    Search does not require credentials.
    Download requires OAuth2 client_id + client_secret.
    """

    def __init__(self, client_id: str = "", client_secret: str = "") -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    @property
    def provider_name(self) -> str:
        return "copernicus"

    @property
    def supported_satellites(self) -> list[str]:
        return ["Sentinel-1", "Sentinel-2"]

    @property
    def is_configured(self) -> bool:
        return True

    @property
    def supports_search_without_credentials(self) -> bool:
        return True

    @property
    def _download_configured(self) -> bool:
        return bool(self._client_id and self._client_secret)

    # ── Search ────────────────────────────────────────────────────────────────

    async def search(self, params: SceneSearchParams) -> list[EOScene]:
        bbox = params.to_bbox()
        collections = self._resolve_collections(params.satellite)
        if not collections:
            return []

        tasks = [
            self._search_collection(collection, bbox, params)
            for collection in collections
        ]
        results_nested = await asyncio.gather(*tasks, return_exceptions=True)

        scenes: list[EOScene] = []
        for result in results_nested:
            if isinstance(result, Exception):
                log.warning("Copernicus collection search error: %s", result)
                continue
            scenes.extend(result)

        # Sort scenes by acquisition date descending
        scenes.sort(key=lambda s: s.acquisition_date, reverse=True)
        return scenes[: params.limit]

    async def _search_collection(
        self,
        collection: str,
        bbox: tuple[float, float, float, float],
        params: SceneSearchParams,
    ) -> list[EOScene]:
        """Run STAC /search query for one collection."""
        payload: dict[str, Any] = {
            "collections": [collection],
            "bbox": list(bbox),
            "datetime": f"{params.date_from.isoformat()}T00:00:00Z/{params.date_to.isoformat()}T23:59:59Z",
            "limit": min(params.limit, 100),
        }

        # Apply cloud cover filter ONLY to optical sensors (Sentinel-2), not Radar (Sentinel-1)
        if "sentinel-2" in collection.lower() and params.cloud_cover_max < 100.0:
            payload["query"] = {
                "eo:cloud_cover": {"lte": params.cloud_cover_max}
            }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(STAC_SEARCH_URL, json=payload)
            if resp.status_code != 200:
                log.warning(
                    "Copernicus STAC search %s returned %s: %s",
                    collection, resp.status_code, resp.text[:200],
                )
                return []

            data = resp.json()

        return [self._stac_item_to_scene(item, collection) for item in data.get("features", [])]

    def _stac_item_to_scene(self, item: dict, collection: str) -> EOScene:
        props = item.get("properties", {})
        geom = item.get("geometry")

        raw_bbox = item.get("bbox")
        if raw_bbox and len(raw_bbox) >= 4:
            scene_bbox = (float(raw_bbox[0]), float(raw_bbox[1]), float(raw_bbox[2]), float(raw_bbox[3]))
        else:
            scene_bbox = (0.0, 0.0, 0.0, 0.0)

        if "sentinel-2" in collection.lower():
            satellite = "Sentinel-2" + str(props.get("platform", "")).replace("sentinel-2", "").replace("SENTINEL-2", "").upper()
            sensor = "MSI"
            bands = _S2_BANDS
            resolution_m = 10.0
            processing_level = props.get("processing:level", "L2A")
        else:
            satellite = "Sentinel-1" + str(props.get("platform", "")).replace("sentinel-1", "").replace("SENTINEL-1", "").upper()
            sensor = "SAR-C"
            bands = _S1_BANDS
            resolution_m = 20.0
            processing_level = "GRD"

        assets = item.get("assets", {})
        source_url = None
        for key in ("product", "download", "data", "Product"):
            if key in assets:
                source_url = assets[key].get("href")
                break

        thumbnail_url = None
        for key in ("thumbnail", "rendered_preview", "quicklook", "overview"):
            if key in assets:
                thumbnail_url = assets[key].get("href")
                if thumbnail_url:
                    break

        acq_raw = props.get("datetime") or props.get("start_datetime", "")
        try:
            acq_date = date.fromisoformat(acq_raw[:10])
        except (ValueError, TypeError):
            acq_date = date.today()

        return EOScene(
            scene_id=item.get("id", ""),
            provider="copernicus",
            satellite=satellite.strip(),
            sensor=sensor,
            acquisition_date=acq_date,
            cloud_cover=props.get("eo:cloud_cover"),
            bbox=scene_bbox,
            footprint_geojson=geom,
            resolution_m=resolution_m,
            source_url=source_url,
            thumbnail_url=thumbnail_url,
            processing_level=processing_level,
            bands=bands,
            metadata={
                "collection": collection,
                "stac_id": item.get("id"),
                "platform": props.get("platform"),
                "instrument": props.get("instruments"),
                "tile_id": props.get("s2:mgrs_tile") or props.get("s1:datatake_id"),
            },
        )

    def _resolve_collections(self, satellite: str | None) -> list[str]:
        if satellite is None:
            return list(_COLLECTIONS.values())
        for key, coll in _COLLECTIONS.items():
            if key.lower() in satellite.lower() or satellite.lower() in key.lower():
                return [coll]
        return []

    # ── Download ──────────────────────────────────────────────────────────────

    async def _get_token(self) -> str:
        import time
        if self._token and time.time() < self._token_expires_at - 30:
            return self._token

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
            )
            if resp.status_code != 200:
                raise EOProviderDownloadError(
                    f"Copernicus token request failed {resp.status_code}: {resp.text[:300]}"
                )
            token_data = resp.json()
            self._token = token_data["access_token"]
            self._token_expires_at = time.time() + token_data.get("expires_in", 600)
            return self._token

    async def download(self, scene: EOScene, dest_path: Path) -> Path:
        if not self._download_configured:
            raise EOProviderUnconfiguredError(
                "Copernicus download requires COPERNICUS_CLIENT_ID and "
                "COPERNICUS_CLIENT_SECRET to be set in backend/.env"
            )
        if not scene.source_url:
            raise EOProviderDownloadError(
                f"Scene {scene.scene_id} has no source_url — cannot download."
            )

        token = await self._get_token()
        dest_path.mkdir(parents=True, exist_ok=True)
        file_path = dest_path / f"{scene.scene_id}.zip"

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=20, read=600, write=None, pool=None),
            follow_redirects=True,
        ) as client:
            async with client.stream(
                "GET",
                scene.source_url,
                headers={"Authorization": f"Bearer {token}"},
            ) as response:
                if response.status_code != 200:
                    raise EOProviderDownloadError(
                        f"Copernicus download failed {response.status_code} for {scene.scene_id}"
                    )
                import aiofiles
                async with aiofiles.open(file_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=65536):
                        await f.write(chunk)

        return file_path
