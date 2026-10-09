"""
Demo Data Generator — Phase 5B.

Creates synthetic before/after satellite scenes + processed index rasters
directly in the shared database and on disk, so the change-detection pipeline
can run immediately without needing real satellite ingestion or Phase 5A processing.

These are clearly labelled as DEMO data (provider='demo') and are safe to
delete from the database at any time.

Synthetic landscape model
--------------------------
The generated 256×256 rasters represent a plausible mixed landscape:
  - Dominant vegetation cover with realistic NDVI (0.3–0.7)
  - A river/water body region with negative NDWI
  - Low urban fringe with slightly positive NDBI

Simulated changes (after scene)
---------------------------------
  - Bottom-right quadrant: NDVI drops, NDBI rises → urban expansion
  - Top-left quadrant:     NDWI rises → water body expansion / flooding
  - Small central patch:   NDVI rises → vegetation recovery / reforestation
"""
from __future__ import annotations

import logging
import uuid
from datetime import date, timedelta
from pathlib import Path
from typing import Tuple

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_bounds
from sqlalchemy.orm import Session
from sqlalchemy import text

log = logging.getLogger(__name__)

# ── Raster dimensions ─────────────────────────────────────────────────────────
DEMO_H, DEMO_W = 256, 256
NODATA_VALUE: float = -9999.0

# Geographic extent — 0.1° × 0.1° box centred on approximate India coordinates.
# These values will be overridden per-location if we have bbox info; for now
# they are always within a valid geographic coordinate range.
_LOC_CENTROIDS: dict = {
    # location_id → (lon_centre, lat_centre)
    "hyderabad":                  (78.4867, 17.3850),
    "godavari":                   (81.0, 16.9),
    "chilika":                    (85.4, 19.7),
    "sundarbans":                 (88.9, 21.9),
    "western_ghats":              (76.5, 11.5),
    "thar_desert":                (71.9, 27.0),
    "brahmaputra_river_basin":    (93.5, 26.5),
}
_DEFAULT_CENTROID = (78.5, 17.4)


def _get_extent(location_id: str) -> Tuple[float, float, float, float]:
    """Return (lon_min, lat_min, lon_max, lat_max) for the demo raster."""
    lon_c, lat_c = _LOC_CENTROIDS.get(location_id.lower(), _DEFAULT_CENTROID)
    half = 0.05  # 0.1° × 0.1° bounding box
    return lon_c - half, lat_c - half, lon_c + half, lat_c + half


def _write_cog(array: np.ndarray, transform, crs: CRS, out_path: Path) -> None:
    """Write a float32 LZW-compressed GeoTIFF."""
    h, w = array.shape
    out_path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver":    "GTiff",
        "dtype":     "float32",
        "count":     1,
        "crs":       crs,
        "transform": transform,
        "height":    h,
        "width":     w,
        "nodata":    NODATA_VALUE,
        "compress":  "lzw",
        "tiled":     True,
        "blockxsize": 64,
        "blockysize": 64,
    }
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(array.astype("float32"), 1)


def _fractal_noise(h: int, w: int, seed: int, octaves: int = 4, persistence: float = 0.5) -> np.ndarray:
    from scipy.ndimage import gaussian_filter
    rng = np.random.default_rng(seed)
    noise = np.zeros((h, w), dtype=np.float32)
    freq = 1.0
    amp = 1.0
    for _ in range(octaves):
        n = rng.normal(0, 1, (h, w))
        sigma = max(1.0, min(h, w) / (8.0 * freq))
        n = gaussian_filter(n, sigma=sigma)
        noise += n * amp
        amp *= persistence
        freq *= 2.0
    # normalize to roughly -1 to 1
    max_val = np.max(np.abs(noise))
    if max_val > 0:
        noise /= max_val
    return noise

def _make_synthetic_indices(seed: int = 42) -> dict:
    """
    Generate realistic organic landscape index arrays.
    Simulates:
      - A natural meandering river corridor (high NDWI, low NDVI/NDBI)
      - Natural forest clusters & hills (high NDVI)
      - Urban settlement patches (high NDBI)
      - Realistic changes: urban sprawl, river level rise, forest degradation
    """
    rng = np.random.default_rng(seed)

    # Coordinate grids normalized [0, 1]
    y, x = np.ogrid[:DEMO_H, :DEMO_W]
    yn, xn = y / float(DEMO_H), x / float(DEMO_W)

    # Base fractal noise for organic terrain
    terrain_noise = _fractal_noise(DEMO_H, DEMO_W, seed)
    forest_noise = _fractal_noise(DEMO_H, DEMO_W, seed + 1)
    urban_noise = _fractal_noise(DEMO_H, DEMO_W, seed + 2)

    # 1. Meandering river curve: y = 0.45 + 0.15 * sin(2*pi*x/W * 1.5) + ... but distorted by noise
    river_center = 0.45 + 0.15 * np.sin(2 * np.pi * xn * 1.5) + 0.05 * np.cos(4 * np.pi * xn)
    river_center += 0.05 * terrain_noise  # Add organic distortion
    dist_to_river = np.abs(yn - river_center)
    river_mask_b = dist_to_river < 0.035
    river_mask_a = dist_to_river < 0.055  # River expansion/flooding in after-scene

    # 2. Forest clusters
    forest_density = np.clip(0.4 + 0.6 * forest_noise, 0, 1)

    # 3. Urban growth center (bottom right)
    dist_to_urban = np.sqrt((xn - 0.75)**2 + (yn - 0.35)**2)
    urban_core = np.clip(1.0 - (dist_to_urban / 0.25) + 0.3 * urban_noise, 0, 1)
    
    # After scene sprawl
    dist_to_sprawl = np.sqrt((xn - 0.65)**2 + (yn - 0.45)**2)
    urban_sprawl = np.clip(1.0 - (dist_to_sprawl / 0.15) + 0.3 * urban_noise, 0, 1)

    # Base arrays with subtle organic spatial variation
    spatial_noise = terrain_noise * 0.1

    # NDVI: high in forests (~0.7), medium in fields (~0.4), low in urban (~0.1), negative in water (~-0.3)
    ndvi_b = 0.35 + 0.4 * forest_density - 0.3 * urban_core + spatial_noise
    ndvi_b[river_mask_b] = -0.25 + rng.normal(0, 0.02, np.sum(river_mask_b))

    # NDWI: high in water (~0.5), negative elsewhere
    ndwi_b = -0.30 + spatial_noise
    ndwi_b[river_mask_b] = 0.45 + rng.normal(0, 0.03, np.sum(river_mask_b))

    # NDBI: high in urban (~0.35), negative in vegetation/water
    ndbi_b = -0.20 + 0.5 * urban_core + spatial_noise
    ndbi_b[river_mask_b] = -0.35

    # ── After-scene with realistic environmental changes ──────────────────────
    ndvi_a = ndvi_b.copy()
    ndwi_a = ndwi_b.copy()
    ndbi_a = ndbi_b.copy()

    # 1. Water expansion / flooding along river banks
    flooded = river_mask_a & ~river_mask_b
    ndwi_a[flooded] = 0.40 + rng.normal(0, 0.03, np.sum(flooded))
    ndvi_a[flooded] = -0.20
    ndbi_a[flooded] = -0.30

    # 2. Urban expansion (sprawl)
    sprawl_pixels = (urban_sprawl > 0.4) & ~river_mask_a
    ndbi_a[sprawl_pixels] = np.maximum(ndbi_a[sprawl_pixels], 0.1 + 0.3 * urban_sprawl[sprawl_pixels])
    ndvi_a[sprawl_pixels] = np.minimum(ndvi_a[sprawl_pixels], 0.1)

    # 3. Forest canopy gain (reforestation patch in north-west)
    reforest = (forest_noise > 0.4) & (yn < 0.25) & (xn < 0.3) & ~river_mask_a
    ndvi_a[reforest] += 0.25

    # Clip to valid index range [-1, 1]
    for arr in (ndvi_b, ndwi_b, ndbi_b, ndvi_a, ndwi_a, ndbi_a):
        np.clip(arr, -1.0, 1.0, out=arr)

    return {
        "NDVI": (ndvi_b.astype("float32"), ndvi_a.astype("float32")),
        "NDWI": (ndwi_b.astype("float32"), ndwi_a.astype("float32")),
        "NDBI": (ndbi_b.astype("float32"), ndbi_a.astype("float32")),
    }


def _write_demo_rgb_image(index_data: dict, out_path: Path, is_after: bool = False) -> None:
    """
    Synthesizes a realistic true-color RGB satellite image from spectral indices.
    Vegetation -> Natural Green
    Water -> Natural Deep Blue/Teal
    Urban/Built-up -> Warm Earthy Gray/Brown
    """
    from PIL import Image
    from scipy.ndimage import gaussian_filter

    idx_key = 1 if is_after else 0
    ndvi = index_data["NDVI"][idx_key]
    ndwi = index_data["NDWI"][idx_key]
    ndbi = index_data["NDBI"][idx_key]

    h, w = ndvi.shape
    
    # Generate some high-frequency noise for realistic satellite texture
    rng = np.random.default_rng(42 if not is_after else 43)
    texture = gaussian_filter(rng.normal(0, 1, (h, w)), sigma=1) * 15
    
    rgb = np.zeros((h, w, 3), dtype=np.float32)

    # Base earth/soil tone (mix of brown and gray)
    rgb[..., 0] = 130 + texture
    rgb[..., 1] = 115 + texture
    rgb[..., 2] = 95 + texture

    # Vegetation (High NDVI -> Natural Forest Green)
    veg_mask = ndvi > 0.2
    veg_factor = np.clip((ndvi - 0.2) / 0.6, 0, 1)[..., None]
    veg_color = np.array([45, 110, 50], dtype=np.float32)
    # Blend vegetation based on NDVI strength
    rgb = np.where(veg_mask[..., None], rgb * (1 - veg_factor) + (veg_color + texture[..., None]*0.5) * veg_factor, rgb)

    # Urban (High NDBI -> Light Urban Concrete/Asphalt)
    urban_mask = (ndbi > 0.1) & ~veg_mask
    urban_factor = np.clip((ndbi - 0.1) / 0.5, 0, 1)[..., None]
    urban_color = np.array([170, 165, 160], dtype=np.float32)
    rgb = np.where(urban_mask[..., None], rgb * (1 - urban_factor) + (urban_color + texture[..., None]) * urban_factor, rgb)

    # Water (High NDWI -> Deep Blue/Teal)
    water_mask = ndwi > 0.1
    water_color = np.array([20, 60, 90], dtype=np.float32)
    # Water absorbs light, less texture
    rgb[water_mask] = water_color + texture[water_mask][..., None] * 0.3

    # Clip and convert to uint8
    rgb_out = np.clip(rgb, 0, 255).astype(np.uint8)

    img = Image.fromarray(rgb_out, mode="RGB")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")



def generate_demo_scenes(
    db: Session,
    location_id: str,
    eo_storage_root: Path,
) -> Tuple[int, int, str, str]:
    """
    Create two demo satellite_scenes and their processed index rasters.

    Steps
    -----
    1. Generate synthetic NDVI/NDWI/NDBI before/after arrays.
    2. Write them as float32 COG GeoTIFFs to ``eo_storage_root/demo/<location_id>/``.
    3. Insert satellite_scenes rows (provider='demo', ingestion_status='completed').
    4. Insert processed_images rows linking each raster to its scene.
    5. Return (before_db_id, after_db_id, before_scene_id, after_scene_id).

    Parameters
    ----------
    db : Session
        SQLAlchemy session — shared DB (same as backend).
    location_id : str
        ClimateX location identifier.
    eo_storage_root : Path
        Root of EO storage tree (EO_STORAGE_PATH from config).
    """
    lon_min, lat_min, lon_max, lat_max = _get_extent(location_id)
    transform = from_bounds(lon_min, lat_min, lon_max, lat_max, DEMO_W, DEMO_H)
    crs = CRS.from_epsg(4326)
    bounds_json = [lon_min, lat_min, lon_max, lat_max]

    today = date.today()
    before_date = today - timedelta(days=365)   # approx 1 year ago
    after_date  = today - timedelta(days=30)    # approx 1 month ago

    index_data = _make_synthetic_indices(seed=42)

    # ── Insert satellite_scenes ───────────────────────────────────────────────
    def insert_scene(acq_date: date, label: str) -> Tuple[int, str]:
        scene_id = f"DEMO-{location_id.upper()[:8]}-{label}-{uuid.uuid4().hex[:6].upper()}"
        row = db.execute(
            text(
                """
                INSERT INTO satellite_scenes
                    (scene_id, provider, satellite, sensor,
                     acquisition_date, cloud_cover, resolution_m,
                     crs, location_id, ingestion_status,
                     bbox_min_lon, bbox_min_lat, bbox_max_lon, bbox_max_lat,
                     scene_metadata, created_at)
                VALUES
                    (:scene_id, 'demo', 'DEMO-SAT-2A', 'MSI',
                     :acq_date, 2.0, 10.0,
                     'EPSG:4326', :loc_id, 'completed',
                     :lon_min, :lat_min, :lon_max, :lat_max,
                     :meta, NOW())
                RETURNING id
                """
            ),
            {
                "scene_id":   scene_id,
                "acq_date":   acq_date.isoformat(),
                "loc_id":     location_id,
                "lon_min":    lon_min,
                "lat_min":    lat_min,
                "lon_max":    lon_max,
                "lat_max":    lat_max,
                "meta":       '{"source": "demo_generator", "synthetic": true}',
            },
        ).fetchone()
        return row[0], scene_id

    log.info("Creating demo satellite scenes for location=%s", location_id)
    before_db_id, before_scene_id = insert_scene(before_date, "BEF")
    after_db_id,  after_scene_id  = insert_scene(after_date,  "AFT")
    db.flush()

    # ── Write rasters and insert processed_images ─────────────────────────────
    demo_dir = eo_storage_root / "demo" / location_id
    demo_dir.mkdir(parents=True, exist_ok=True)

    # Generate True-Color RGB Satellite Images for Before & After scenes
    _write_demo_rgb_image(index_data, demo_dir / "before_rgb.png", is_after=False)
    _write_demo_rgb_image(index_data, demo_dir / "after_rgb.png", is_after=True)

    for index_name, (arr_before, arr_after) in index_data.items():
        for db_id, arr, label in [
            (before_db_id, arr_before, "before"),
            (after_db_id,  arr_after,  "after"),
        ]:
            rel_path = f"demo/{location_id}/{label}_{index_name.lower()}.tif"
            out_path = eo_storage_root / rel_path
            _write_cog(arr, transform, crs, out_path)
            log.info("Wrote demo raster: %s", out_path)

            db.execute(
                text(
                    """
                    INSERT INTO processed_images
                        (scene_id, index_name, file_path, resolution_m,
                         crs, bounds, status, completed_at, created_at)
                    VALUES
                        (:sid, :idx, :path, 10.0,
                         'EPSG:4326', :bounds, 'completed', NOW(), NOW())
                    """
                ),
                {
                    "sid":    db_id,
                    "idx":    index_name,
                    "path":   rel_path,
                    "bounds": str(bounds_json).replace("'", '"'),
                },
            )

    db.commit()
    log.info(
        "Demo scenes created: before_id=%d (%s) after_id=%d (%s)",
        before_db_id, before_scene_id, after_db_id, after_scene_id,
    )
    return before_db_id, after_db_id, before_scene_id, after_scene_id
