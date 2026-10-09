"""
EO Gateway — provider abstraction layer for satellite Earth Observation data.

Supported providers:
  - Copernicus Data Space (Sentinel-1 GRD, Sentinel-2 L2A)  [search: public, download: OAuth2]
  - USGS M2M (Landsat 8/9)                                   [requires free account]
  - UP42 (multi-source commercial catalog)                   [requires project credentials]

Usage:
    from app.eo_gateway import get_registry, SceneSearchParams, EOScene
    registry = get_registry()
    scenes = await registry.search_all_providers(params)
"""

from .base import (  # noqa: F401
    AbstractEOProvider,
    SceneSearchParams,
    EOScene,
    EOProviderError,
    EOProviderUnconfiguredError,
    EOProviderDownloadError,
)
from .registry import (  # noqa: F401
    get_registry,
    init_registry,
    build_registry,
    ProviderRegistry,
)
from . import registry  # noqa: F401
