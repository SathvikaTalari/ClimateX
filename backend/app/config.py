from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    app_env: str = "development"
    secret_key: str = "dev-secret-key"
    backend_port: int = 8000

    # PostgreSQL
    database_url: str = "postgresql://climatex_user:climatex_pass@localhost:5432/climatex"

    # CORS
    frontend_url: str = "http://localhost:3000"

    # ─── Phase 4: EO Provider Credentials (all optional) ─────────────────────
    # Copernicus Data Space (Sentinel-1, Sentinel-2)
    # Search is public; download requires OAuth2 client credentials
    copernicus_client_id: str = ""
    copernicus_client_secret: str = ""

    # USGS Machine-to-Machine API (Landsat 8/9)
    # Register free at https://ers.cr.usgs.gov
    usgs_username: str = ""
    usgs_password: str = ""

    # UP42 (multi-source commercial catalog)
    up42_project_id: str = ""
    up42_project_api_key: str = ""

    # ─── Phase 5B: ML Service ────────────────────────────────────────────────
    # URL of the separate ML service (change detection)
    ml_service_url: str = "http://localhost:8001"

    # ─── Phase 4: EO Storage ─────────────────────────────────────────────────
    # Local path for downloaded raster files (relative to backend dir)
    eo_storage_path: str = "./eo_data"
    # Maximum raster file size in MB allowed for ingestion
    max_scene_file_size_mb: int = 500

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            self.frontend_url,
        ]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
