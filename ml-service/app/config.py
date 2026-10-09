"""
ML Service Configuration — Phase 5B.

All settings are read from environment variables (or a .env file).
Copy .env.example to .env and adjust paths before starting the service.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class MLSettings(BaseSettings):
    # Application
    app_env: str = "development"
    ml_service_port: int = 8001

    # PostgreSQL — same DB as the FastAPI backend
    database_url: str = (
        "postgresql://climatex_user:climatex_pass@127.0.0.1:5433/climatex"
    )

    # Storage
    # Root of Phase 5A processed rasters produced by the backend
    eo_storage_path: str = "../backend/eo_data"
    # Where this service writes change-map GeoTIFFs
    ml_storage_path: str = "../backend/eo_data/change_maps"

    # Backend URL (for optional reverse calls; not used in Phase 5B)
    backend_url: str = "http://localhost:8000"

    # ─── Algorithm Parameters ────────────────────────────────────────────────
    # Threshold multiplier for μ ± k·σ spectral change detection.
    # Lowering this makes detection more sensitive (more false positives).
    # Raising this makes it more conservative (misses subtle changes).
    k_sigma: float = 1.5

    # Minimum connected-component area (pixels) to suppress speckle / salt-and-pepper noise.
    # At 10 m Sentinel-2 resolution: 9 px ≈ 900 m².
    min_change_area_px: int = 9

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]


@lru_cache()
def get_settings() -> MLSettings:
    return MLSettings()
