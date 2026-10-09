"""
UP42 adapter — multi-source commercial EO catalog.

API:    https://api.up42.com/
Auth:   Project ID + Project API Key (OAuth2 client credentials)

UP42 offers a catalog search across many satellites including Pléiades,
SPOT, SuperView, and many more.  A free/starter account gives limited
catalog access.

Reference:
  https://docs.up42.com/developers/api-catalog
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

UP42_TOKEN_URL = "https://api.up42.com/oauth/token"
UP42_CATALOG_URL = "https://api.up42.com/catalog/stac/search"


class UP42Provider(AbstractEOProvider):
    """
    Searches the UP42 multi-source EO catalog.
    Both search and download require project credentials.
    """

    def __init__(self, project_id: str = "", project_api_key: str = "") -> None:
        self._project_id = project_id
        self._project_api_key = project_api_key
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    # ── Identity ──────────────────────────────────────────────────────────────

    @property
    def provider_name(self) -> str:
        return "up42"

    @property
    def supported_satellites(self) -> list[str]:
        # UP42 aggregates many sources; we list the most common
        return [
            "Sentinel-1", "Sentinel-2",
            "Landsat-8", "Landsat-9",
            "Pleiades", "SPOT",
        ]

    @property
    def is_configured(self) -> bool:
        return bool(self._project_id and self._project_api_key)

    # ── Auth ──────────────────────────────────────────────────────────────────

    async def _get_token(self) -> str:
        import time
        if self._token and time.time() < self._token_expires_at - 30:
            return self._token

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                UP42_TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._project_id,
                    "client_secret": self._project_api_key,
                },
            )
            if resp.status_code != 200:
                raise EOProviderError(
                    f"UP42 auth failed {resp.status_code}: {resp.text[:200]}"
                )
            td = resp.json()
            self._token = td["access_token"]
            import time as _t
            self._token_expires_at = _t.time() + td.get("expires_in", 600)
            return self._token  # type: ignore[return-value]

    # ── Search ────────────────────────────────────────────────────────────────

    async def search(self, params: SceneSearchParams) -> list[EOScene]:
        if not self.is_configured:
            raise EOProviderUnconfiguredError(
                "UP42 requires UP42_PROJECT_ID and UP42_PROJECT_API_KEY in backend/.env"
            )

        bbox = params.to_bbox()
        token = await self._get_token()

        # Build STAC-compatible search body
        body: dict[str, Any] = {
            "bbox": list(bbox),
            "datetime": (
                f"{params.date_from.isoformat()}T00:00:00Z"
                f"/{params.date_to.isoformat()}T23:59:59Z"
            ),
            "limit": min(params.limit, 50),
        }
        if params.cloud_cover_max < 100.0:
            body["query"] = {"eo:cloud_cover": {"lte": params.cloud_cover_max}}

        # Filter by satellite / collection if specified
        if params.satellite:
            body["collections"] = self._resolve_collections(params.satellite)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    UP42_CATALOG_URL,
                    json=body,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                )
                if resp.status_code != 200:
                    log.warning("UP42 catalog search %s: %s", resp.status_code, resp.text[:200])
                    return []
                data = resp.json()
        except httpx.HTTPError as exc:
            log.warning("UP42 HTTP error: %s", exc)
            return []

        return [self._stac_item_to_scene(item) for item in data.get("features", [])]

    def _stac_item_to_scene(self, item: dict) -> EOScene:
        props = item.get("properties", {})
        raw_bbox = item.get("bbox", [0, 0, 0, 0])
        bbox_val: tuple[float, float, float, float] = (
            raw_bbox[0], raw_bbox[1], raw_bbox[2], raw_bbox[3]
        )

        acq_raw = props.get("datetime") or ""
        try:
            acq_date = date.fromisoformat(acq_raw[:10])
        except (ValueError, TypeError):
            acq_date = date.today()

        platform = props.get("platform", "unknown")
        instrument = ", ".join(props.get("instruments", []))
        collection = item.get("collection", "")

        return EOScene(
            scene_id=item.get("id", ""),
            provider="up42",
            satellite=platform,
            sensor=instrument or "Unknown",
            acquisition_date=acq_date,
            cloud_cover=props.get("eo:cloud_cover"),
            bbox=bbox_val,
            footprint_geojson=item.get("geometry"),
            resolution_m=props.get("gsd"),
            source_url=item.get("assets", {}).get("download", {}).get("href"),
            processing_level=props.get("processing:level"),
            bands=[b.get("name", "") for b in props.get("eo:bands", [])],
            metadata={
                "collection": collection,
                "stac_id": item.get("id"),
                "platform": platform,
                "up42_order_id": props.get("up42-order:id"),
            },
        )

    def _resolve_collections(self, satellite: str) -> list[str]:
        """Return UP42 collection names for the given satellite hint."""
        s = satellite.lower()
        mapping = {
            "sentinel-1": ["sentinel-1-grd"],
            "sentinel-2": ["sentinel-2-l2a"],
            "landsat": ["landsat-8-l2", "landsat-9-l2"],
            "pleiades": ["phr"],
            "spot": ["spo"],
        }
        for key, cols in mapping.items():
            if key in s:
                return cols
        return []

    # ── Download ──────────────────────────────────────────────────────────────

    async def download(self, scene: EOScene, dest_path: Path) -> Path:
        if not self.is_configured:
            raise EOProviderUnconfiguredError(
                "UP42 download requires UP42_PROJECT_ID and UP42_PROJECT_API_KEY in backend/.env"
            )
        if not scene.source_url:
            raise EOProviderDownloadError(
                f"Scene {scene.scene_id} from UP42 has no download URL. "
                "An UP42 order may be required for commercial imagery."
            )

        token = await self._get_token()
        dest_path.mkdir(parents=True, exist_ok=True)
        file_path = dest_path / f"{scene.scene_id}.tif"

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=20, read=600, write=None, pool=None),
            follow_redirects=True,
        ) as client:
            async with client.stream(
                "GET",
                scene.source_url,
                headers={"Authorization": f"Bearer {token}"},
            ) as resp:
                if resp.status_code != 200:
                    raise EOProviderDownloadError(
                        f"UP42 download HTTP {resp.status_code} for {scene.scene_id}"
                    )
                import aiofiles
                async with aiofiles.open(file_path, "wb") as f:
                    async for chunk in resp.aiter_bytes(65536):
                        await f.write(chunk)

        return file_path
