"""
USGS M2M (Machine-to-Machine) API adapter — Landsat 8 & 9.

API:  https://m2m.cr.usgs.gov/api/api/json/stable/
Auth: Username + password (free account at https://ers.cr.usgs.gov)

Supports Landsat Collection 2 Level-2 (surface reflectance/temperature).

Reference:
  https://m2m.cr.usgs.gov/api/docs/json/
"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Any

import httpx

from .base import (
    AbstractEOProvider,
    EOProviderDownloadError,
    EOProviderError,
    EOProviderUnconfiguredError,
    EOScene,
    SceneSearchParams,
)

log = logging.getLogger(__name__)

M2M_BASE = "https://m2m.cr.usgs.gov/api/api/json/stable/"

# Dataset names in USGS EarthExplorer / M2M
_DATASET_MAP: dict[str, str] = {
    "landsat-8": "landsat_ot_c2_l2",   # Landsat Collection 2 Level-2 (OLI-TIRS)
    "landsat-9": "landsat_ot_c2_l2",   # Same dataset; L9 scenes mixed in
}

# OLI-TIRS (Landsat 8/9) band list for L2
_LANDSAT_BANDS = ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7", "ST_B10", "QA_PIXEL"]


class USGSProvider(AbstractEOProvider):
    """
    Searches Landsat 8/9 scenes via the USGS M2M JSON API.
    Requires a free USGS ERS account (username + password).
    """

    def __init__(self, username: str = "", password: str = "") -> None:
        self._username = username
        self._password = password
        self._api_key: str | None = None

    # ── Identity ──────────────────────────────────────────────────────────────

    @property
    def provider_name(self) -> str:
        return "usgs"

    @property
    def supported_satellites(self) -> list[str]:
        return ["Landsat-8", "Landsat-9"]

    @property
    def is_configured(self) -> bool:
        return bool(self._username and self._password)

    # ── Auth ──────────────────────────────────────────────────────────────────

    async def _login(self) -> str:
        """Authenticate and return an M2M API key (session token)."""
        if self._api_key:
            return self._api_key

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                M2M_BASE + "login",
                json={"username": self._username, "password": self._password},
            )
            data = resp.json()
            if resp.status_code != 200 or data.get("errorCode"):
                raise EOProviderError(
                    f"USGS M2M login failed: {data.get('errorMessage', resp.text[:200])}"
                )
            self._api_key = data["data"]
            return self._api_key  # type: ignore[return-value]

    async def _post(self, endpoint: str, payload: dict) -> dict:
        api_key = await self._login()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                M2M_BASE + endpoint,
                json=payload,
                headers={"X-Auth-Token": api_key},
            )
            data = resp.json()
            if data.get("errorCode"):
                raise EOProviderError(
                    f"USGS M2M {endpoint} error: {data.get('errorMessage')}"
                )
            return data  # type: ignore[return-value]

    # ── Search ────────────────────────────────────────────────────────────────

    async def search(self, params: SceneSearchParams) -> list[EOScene]:
        if not self.is_configured:
            raise EOProviderUnconfiguredError(
                "USGS provider requires USGS_USERNAME and USGS_PASSWORD in backend/.env"
            )

        bbox = params.to_bbox()
        # Determine which Landsat sensors to query
        satellite_filter = (params.satellite or "").lower()
        datasets = set()
        if not satellite_filter or "landsat" in satellite_filter:
            datasets.add("landsat_ot_c2_l2")
        if not datasets:
            return []

        all_scenes: list[EOScene] = []
        for dataset in datasets:
            scenes = await self._search_dataset(dataset, bbox, params)
            all_scenes.extend(scenes)

        return all_scenes[: params.limit]

    async def _search_dataset(
        self,
        dataset_name: str,
        bbox: tuple[float, float, float, float],
        params: SceneSearchParams,
    ) -> list[EOScene]:
        payload: dict[str, Any] = {
            "datasetName": dataset_name,
            "sceneFilter": {
                "acquisitionFilter": {
                    "start": params.date_from.isoformat(),
                    "end": params.date_to.isoformat(),
                },
                "spatialFilter": {
                    "filterType": "mbr",
                    "lowerLeft": {"latitude": bbox[1], "longitude": bbox[0]},
                    "upperRight": {"latitude": bbox[3], "longitude": bbox[2]},
                },
                "cloudCoverFilter": {
                    "max": int(params.cloud_cover_max),
                    "includeUnknown": True,
                },
            },
            "maxResults": min(params.limit, 100),
            "startingNumber": 1,
        }

        try:
            data = await self._post("scene-search", payload)
        except EOProviderError as exc:
            log.warning("USGS scene-search error: %s", exc)
            return []

        results = data.get("data", {}).get("results", [])
        return [self._usgs_result_to_scene(r, dataset_name) for r in results]

    def _usgs_result_to_scene(self, r: dict, dataset_name: str) -> EOScene:
        display_id = r.get("displayId", r.get("entityId", ""))
        # Determine Landsat version from scene ID prefix
        satellite = "Landsat-9" if display_id.startswith("LC09") else "Landsat-8"
        sensor = "OLI-TIRS"

        # Spatial bounds
        sb = r.get("spatialBounds", {}).get("coordinates", [[[]]])[0]
        lons = [pt[0] for pt in sb] if sb else [0.0]
        lats = [pt[1] for pt in sb] if sb else [0.0]
        bbox_val: tuple[float, float, float, float] = (min(lons), min(lats), max(lons), max(lats))

        # Build GeoJSON footprint from spatial bounds
        footprint: dict | None = None
        if sb:
            footprint = {"type": "Polygon", "coordinates": [sb]}

        acq_raw = r.get("temporalCoverage", {}).get("startDate", "")
        try:
            acq_date = date.fromisoformat(acq_raw[:10])
        except (ValueError, TypeError):
            acq_date = date.today()

        cloud = r.get("cloudCover")
        try:
            cloud_cover = float(cloud) if cloud is not None else None
        except (ValueError, TypeError):
            cloud_cover = None

        return EOScene(
            scene_id=display_id,
            provider="usgs",
            satellite=satellite,
            sensor=sensor,
            acquisition_date=acq_date,
            cloud_cover=cloud_cover,
            bbox=bbox_val,
            footprint_geojson=footprint,
            resolution_m=30.0,
            source_url=None,  # Requires separate download-options call
            processing_level="L2",
            bands=_LANDSAT_BANDS,
            metadata={
                "entity_id": r.get("entityId"),
                "display_id": display_id,
                "dataset": dataset_name,
                "browse": r.get("browse", [{}])[0].get("browsePath") if r.get("browse") else None,
                "publish_date": r.get("publishDate"),
            },
        )

    # ── Download ──────────────────────────────────────────────────────────────

    async def download(self, scene: EOScene, dest_path: Path) -> Path:
        if not self.is_configured:
            raise EOProviderUnconfiguredError(
                "USGS download requires USGS_USERNAME and USGS_PASSWORD in backend/.env"
            )
        # Step 1: Get download options
        entity_id = scene.metadata.get("entity_id", scene.scene_id)
        dataset_name = scene.metadata.get("dataset", "landsat_ot_c2_l2")
        data = await self._post(
            "download-options",
            {"datasetName": dataset_name, "entityIds": [entity_id]},
        )
        options = data.get("data", [])
        download_id: str | None = None
        for opt in options:
            if opt.get("available") and opt.get("productName", "").startswith("Landsat Collection"):
                download_id = str(opt["downloadSystem"])
                break

        if not download_id:
            raise EOProviderDownloadError(
                f"No downloadable product found for USGS scene {scene.scene_id}"
            )

        # Step 2: Request download URL
        dl_data = await self._post(
            "download-request",
            {
                "downloads": [{"entityId": entity_id, "productId": download_id}],
                "label": f"climatex-{entity_id}",
            },
        )
        url = dl_data.get("data", {}).get("availableDownloads", [{}])[0].get("url")
        if not url:
            raise EOProviderDownloadError(
                f"USGS did not return a download URL for {scene.scene_id}"
            )

        # Step 3: Stream download
        dest_path.mkdir(parents=True, exist_ok=True)
        file_path = dest_path / f"{scene.scene_id}.tar"
        api_key = await self._login()
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=20, read=600, write=None, pool=None),
            follow_redirects=True,
        ) as client:
            async with client.stream("GET", url, headers={"X-Auth-Token": api_key}) as resp:
                if resp.status_code != 200:
                    raise EOProviderDownloadError(
                        f"USGS download HTTP {resp.status_code} for {scene.scene_id}"
                    )
                import aiofiles
                async with aiofiles.open(file_path, "wb") as f:
                    async for chunk in resp.aiter_bytes(65536):
                        await f.write(chunk)

        return file_path
