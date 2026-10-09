from .health import router as health_router
from .domains import router as domains_router
from .locations import router as locations_router
from .observations import router as observations_router
from .satellite_scenes import router as satellite_scenes_router
from .eo_processing import router as eo_processing_router
from .ml_proxy import router as ml_proxy_router

__all__ = [
    "health_router",
    "domains_router",
    "locations_router",
    "observations_router",
    "satellite_scenes_router",
    "eo_processing_router",
    "ml_proxy_router",
]
