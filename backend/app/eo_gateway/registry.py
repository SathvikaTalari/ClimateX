"""
Provider registry — factory and multi-provider search orchestration.

Usage (in FastAPI startup or dependency):
    from app.eo_gateway.registry import get_registry, ProviderRegistry
    registry = get_registry(settings)
    scenes = await registry.search_all_providers(params)
"""

from __future__ import annotations

import asyncio
import logging
from functools import lru_cache
from typing import TYPE_CHECKING

from .base import AbstractEOProvider, EOScene, EOProviderError, SceneSearchParams
from .copernicus import CopernicusProvider
from .usgs import USGSProvider
from .up42 import UP42Provider

if TYPE_CHECKING:
    from app.config import Settings

log = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Holds all configured EO provider instances and dispatches searches.
    """

    def __init__(self, providers: list[AbstractEOProvider]) -> None:
        self._providers = providers

    @property
    def providers(self) -> list[AbstractEOProvider]:
        return self._providers

    def get_provider(self, name: str) -> AbstractEOProvider | None:
        for p in self._providers:
            if p.provider_name == name:
                return p
        return None

    def available_provider_names(self) -> list[str]:
        return [p.provider_name for p in self._providers]

    def available_satellites(self) -> list[str]:
        """Deduplicated list of satellite names across all providers."""
        seen: set[str] = set()
        result: list[str] = []
        for p in self._providers:
            for sat in p.supported_satellites:
                if sat not in seen:
                    seen.add(sat)
                    result.append(sat)
        return result

    async def search_all_providers(
        self,
        params: SceneSearchParams,
        *,
        providers: list[str] | None = None,
    ) -> list[EOScene]:
        """
        Search all (or specified) available providers in parallel and merge results.

        Args:
            params:    Scene search parameters.
            providers: Optional list of provider names to restrict the search to.
                       Defaults to all configured providers.

        Returns:
            Merged, deduplicated list of EOScene results sorted by acquisition_date desc.
        """
        targets = self._providers
        if providers:
            targets = [p for p in self._providers if p.provider_name in providers]

        if not targets:
            log.warning("No configured providers match the search request.")
            return []

        tasks = [self._safe_search(provider, params) for provider in targets]
        results_nested = await asyncio.gather(*tasks)

        # Merge and deduplicate on (provider, scene_id)
        seen: set[tuple[str, str]] = set()
        merged: list[EOScene] = []
        for scenes in results_nested:
            for scene in scenes:
                key = (scene.provider, scene.scene_id)
                if key not in seen:
                    seen.add(key)
                    merged.append(scene)

        # Sort by acquisition date descending
        merged.sort(key=lambda s: s.acquisition_date, reverse=True)
        return merged

    async def _safe_search(
        self, provider: AbstractEOProvider, params: SceneSearchParams
    ) -> list[EOScene]:
        """Run a provider search; return [] on any error (logged)."""
        try:
            return await provider.search(params)
        except EOProviderError as exc:
            log.warning("[%s] search error: %s", provider.provider_name, exc)
            return []
        except Exception as exc:
            log.exception("[%s] unexpected error during search: %s", provider.provider_name, exc)
            return []


def build_registry(settings: "Settings") -> ProviderRegistry:
    """
    Instantiate and configure all providers from application settings.
    Providers missing required credentials are excluded automatically.
    """
    providers: list[AbstractEOProvider] = []

    # ── Copernicus (Sentinel-1 / Sentinel-2) ──────────────────────────────────
    # Search is always public; we include this provider unconditionally.
    copernicus = CopernicusProvider(
        client_id=settings.copernicus_client_id,
        client_secret=settings.copernicus_client_secret,
    )
    providers.append(copernicus)
    log.info(
        "[EO Registry] Copernicus provider loaded (download_configured=%s)",
        copernicus._download_configured,
    )

    # ── USGS M2M (Landsat 8/9) ────────────────────────────────────────────────
    usgs = USGSProvider(
        username=settings.usgs_username,
        password=settings.usgs_password,
    )
    if usgs.is_configured:
        providers.append(usgs)
        log.info("[EO Registry] USGS provider loaded.")
    else:
        log.info(
            "[EO Registry] USGS provider skipped — USGS_USERNAME / USGS_PASSWORD not set."
        )

    # ── UP42 ──────────────────────────────────────────────────────────────────
    up42 = UP42Provider(
        project_id=settings.up42_project_id,
        project_api_key=settings.up42_project_api_key,
    )
    if up42.is_configured:
        providers.append(up42)
        log.info("[EO Registry] UP42 provider loaded.")
    else:
        log.info(
            "[EO Registry] UP42 provider skipped — UP42_PROJECT_ID / UP42_PROJECT_API_KEY not set."
        )

    return ProviderRegistry(providers)


# ── Singleton cache ───────────────────────────────────────────────────────────

_registry: ProviderRegistry | None = None


def get_registry() -> ProviderRegistry:
    """
    Returns the application-level ProviderRegistry singleton.
    Call init_registry(settings) once at application startup before using this.
    """
    if _registry is None:
        raise RuntimeError(
            "EO registry has not been initialized. "
            "Call init_registry(settings) at application startup."
        )
    return _registry


def init_registry(settings: "Settings") -> ProviderRegistry:
    """Initialize the singleton registry from settings. Called in app lifespan."""
    global _registry
    _registry = build_registry(settings)
    return _registry
