from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import engine, SessionLocal, Base
from .seed import seed_database
from .eo_gateway.registry import init_registry
from .routers import (
    health_router,
    domains_router,
    locations_router,
    observations_router,
    satellite_scenes_router,
    eo_processing_router,
    ml_proxy_router,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables, initialize EO provider registry, and seed initial data on startup."""
    # Initialize EO provider registry
    init_registry(settings)

    # Import all models so Base.metadata is aware of them
    from .models import (  # noqa: F401
        User, Role, user_roles,
        EnvironmentalDomain,
        AdministrativeArea, Location, LocationKeyStat,
        Dataset,
        SatelliteScene,
        Observation,
        ProcessedImage, SpatialFeature,
    )
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database(db)
    yield
    # (shutdown cleanup can go here in the future)


app = FastAPI(
    title="ClimateX API",
    description=(
        "Backend API for the ClimateX Environmental Intelligence Platform. "
        "Provides environmental domain data, monitored locations, satellite scenes, "
        "and earth observation measurements."
    ),
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ─── API v1 Routers ───────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(health_router,          prefix=API_PREFIX)
app.include_router(domains_router,         prefix=API_PREFIX)
app.include_router(locations_router,       prefix=API_PREFIX)
app.include_router(observations_router,    prefix=API_PREFIX)
app.include_router(satellite_scenes_router, prefix=API_PREFIX)
app.include_router(eo_processing_router,   prefix=API_PREFIX)
app.include_router(ml_proxy_router,        prefix=API_PREFIX)


@app.get("/", include_in_schema=False)
def root():
    return {
        "service": "ClimateX API",
        "version": "0.1.0",
        "docs": "/api/docs",
    }
