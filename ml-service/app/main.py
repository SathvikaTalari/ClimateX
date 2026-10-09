"""
ClimateX ML Service — Phase 5B.

A separate FastAPI application that provides satellite change-detection
analysis using the MISCD (Multi-Index Spectral Change Detection) algorithm.

This service:
  - Is independent from the main ClimateX FastAPI backend.
  - Shares the same PostgreSQL database (reads backend tables, owns ml_* tables).
  - Reads Phase 5A processed COG rasters from the shared eo_data/ directory.
  - Exposes results via REST endpoints that the backend proxies to the frontend.

Ports:
  - ML Service: 8001
  - Backend:    8000
  - Frontend:   3000
"""
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import Base, engine
from .routers import ml_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create ML-specific tables on startup."""
    log.info("ML Service starting up — creating tables if needed...")
    from .models import MLAnalysisJob, MLResult  # noqa: F401
    Base.metadata.create_all(bind=engine)
    log.info("ML Service ready on port %d", settings.ml_service_port)
    yield
    log.info("ML Service shutting down.")


app = FastAPI(
    title="ClimateX ML Service",
    description=(
        "Satellite change-detection service for the ClimateX Environmental "
        "Intelligence Platform.\n\n"
        "**Current algorithm**: Multi-Index Spectral Change Detection (MISCD v1.0.0) — "
        "a rigorous, unsupervised threshold-based spectral analysis using NDVI, NDWI, "
        "and NDBI indices computed from Phase 5A processed Sentinel-2 / Landsat rasters.\n\n"
        "**Model roadmap**: TransSiamUNet (Siamese + Transformer + U-Net) training pipeline "
        "is scaffolded for Phase 5C, pending GPU compute and OSCD/LEVIR-CD dataset "
        "preparation. The evaluation framework (Precision/Recall/F1/IoU/Accuracy) "
        "is already wired in and will auto-populate once a trained checkpoint is available.\n\n"
        "**Data integrity**: No fake predictions or confidence values are generated. "
        "\`evaluation_metrics\` is always \`null\` unless a labelled ground-truth mask "
        "is supplied."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ─── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(ml_router)


@app.get("/", include_in_schema=False)
def root():
    return {
        "service": "ClimateX ML Service",
        "version": "1.0.0",
        "algorithm": "MISCD v1.0.0 (threshold_based_spectral_analysis)",
        "algorithm_roadmap": "TransSiamUNet (supervised, Phase 5C — requires training)",
        "evaluation_metrics": "Precision/Recall/F1/IoU/Accuracy (populated when GT available)",
        "docs": "/api/docs",
    }
