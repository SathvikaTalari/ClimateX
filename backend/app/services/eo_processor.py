"""
Earth Observation Processing Service — Phase 5A
Handles:
  - Environmental Index computation (NDVI, NDWI, NDBI, LST)
  - RGB / False-Color Composite PNG generation
  - COG Histogram computation (32-bin pixel distribution)
  - Spatial clipping and zonal statistics
  - COG GeoTIFF output with LZW compression
"""
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

import numpy as np
import rasterio
from rasterio.mask import mask as rasterio_mask
from shapely.geometry import box, mapping

from app.config import get_settings
from app.models.satellite import SatelliteScene
from app.models.location import Location

log = logging.getLogger(__name__)
settings = get_settings()


# ─── Histogram Result ─────────────────────────────────────────────────────────

class HistogramResult:
    """32-bin histogram of index pixel values."""
    def __init__(self, counts: List[int], bin_edges: List[float], index_name: str):
        self.counts = counts
        self.bin_edges = bin_edges
        self.index_name = index_name
        self.total_pixels = sum(counts)

    def to_dict(self) -> Dict[str, Any]:
        # Build midpoint labels for each bin
        midpoints = [
            round((self.bin_edges[i] + self.bin_edges[i + 1]) / 2, 4)
            for i in range(len(self.bin_edges) - 1)
        ]
        return {
            "index_name": self.index_name,
            "counts": self.counts,
            "bin_edges": [round(e, 4) for e in self.bin_edges],
            "bin_midpoints": midpoints,
            "total_pixels": self.total_pixels,
            "num_bins": len(self.counts),
        }


# ─── Main Processor ───────────────────────────────────────────────────────────

class EOProcessor:
    """
    Modular satellite raster processing engine.
    Supports Sentinel-2 MSI, Sentinel-1 SAR, Landsat-8/9 OLI-TIRS.
    """

    def __init__(self, storage_root: Optional[Path] = None):
        self.storage_root = storage_root or Path(settings.eo_storage_path)

    # ── Clipping Helper ──────────────────────────────────────────────────────

    def _clip_to_location(
        self,
        src: rasterio.DatasetReader,
        location: Optional[Location],
    ) -> Tuple[np.ndarray, Any]:
        """Clip raster to a ~0.1° bounding box around a location. Returns (array, transform)."""
        if location is None:
            return src.read(), src.transform

        geom = box(
            location.longitude - 0.05,
            location.latitude - 0.05,
            location.longitude + 0.05,
            location.latitude + 0.05,
        )
        try:
            out_image, out_transform = rasterio_mask(src, [mapping(geom)], crop=True)
            return out_image, out_transform
        except Exception as exc:
            log.warning("Clipping failed (%s) — using full extent.", exc)
            return src.read(), src.transform

    # ── Band-index mapping ───────────────────────────────────────────────────

    def _resolve_bands(
        self,
        scene: SatelliteScene,
        n_bands: int,
    ) -> Dict[str, int]:
        """
        Returns 1-indexed band numbers for red, green, nir, swir.
        Falls back to Sentinel-2 positional defaults.
        """
        band_mapping = {b.upper(): i + 1 for i, b in enumerate(scene.bands or [])}

        def find(keys, fallback):
            for k in keys:
                if k in band_mapping:
                    idx = band_mapping[k]
                    return idx if idx <= n_bands else fallback
            return min(fallback, n_bands)

        return {
            "blue":  find(["B02", "BLUE"],  1),
            "green": find(["B03", "GREEN"], 2),
            "red":   find(["B04", "RED"],   3),
            "nir":   find(["B08", "NIR"],   min(4, n_bands)),
            "swir":  find(["B11", "SWIR1", "SWIR"], min(5, n_bands)),
        }

    # ── COG output helper ────────────────────────────────────────────────────

    def _write_cog(
        self,
        src_profile: Dict,
        out_transform: Any,
        array_2d: np.ndarray,
        out_path: Path,
        nodata: float = -9999.0,
    ) -> None:
        """Write a single-band float32 Cloud-Optimised GeoTIFF."""
        h, w = array_2d.shape[:2]
        use_tiling = h >= 16 and w >= 16

        kwargs = dict(src_profile)
        kwargs.update(
            dtype=rasterio.float32,
            count=1,
            driver="GTiff",
            compress="lzw",
            nodata=nodata,
            transform=out_transform,
            height=h,
            width=w,
        )
        if use_tiling:
            bx = 256 if w >= 256 else max(16, (w // 16) * 16)
            by = 256 if h >= 256 else max(16, (h // 16) * 16)
            kwargs.update(tiled=True, blockxsize=bx, blockysize=by)
        else:
            for k in ("tiled", "blockxsize", "blockysize"):
                kwargs.pop(k, None)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(out_path, "w", **kwargs) as dst:
            dst.write(array_2d.astype("float32"), 1)

    # ── Index Processing ─────────────────────────────────────────────────────

    def process_index(
        self,
        scene: SatelliteScene,
        index_name: str,
        location: Optional[Location] = None,
    ) -> Tuple[Path, Dict[str, Any]]:
        """
        Compute NDVI / NDWI / NDBI / LST for a satellite scene.
        Returns (relative_output_path, zonal_statistics_dict).
        """
        if not scene.file_path:
            raise ValueError(f"Scene {scene.scene_id} has no file_path.")

        index_name = index_name.upper()
        if index_name not in ("NDVI", "NDWI", "NDBI", "LST"):
            raise ValueError(f"Unsupported index: {index_name}. Supported: NDVI, NDWI, NDBI, LST")

        file_path = self.storage_root / scene.file_path
        if not file_path.exists():
            raise FileNotFoundError(f"Raster file not found: {file_path}")

        with rasterio.open(file_path) as src:
            out_image, out_transform = self._clip_to_location(src, location)
            bands = self._resolve_bands(scene, out_image.shape[0])

            nodata_val = src.nodata

            def get_band(idx: int) -> np.ndarray:
                arr = out_image[idx - 1].astype("float32")
                if nodata_val is not None:
                    arr[arr == nodata_val] = np.nan
                return arr

            # ── Compute index ────────────────────────────────────────────────
            if index_name == "NDVI":
                nir = get_band(bands["nir"])
                red = get_band(bands["red"])
                denom = nir + red
                index_array = np.divide(nir - red, denom, out=np.zeros_like(nir), where=denom != 0)

            elif index_name == "NDWI":
                green = get_band(bands["green"])
                nir = get_band(bands["nir"])
                denom = green + nir
                index_array = np.divide(green - nir, denom, out=np.zeros_like(green), where=denom != 0)

            elif index_name == "NDBI":
                swir = get_band(bands["swir"])
                nir = get_band(bands["nir"])
                denom = swir + nir
                index_array = np.divide(swir - nir, denom, out=np.zeros_like(swir), where=denom != 0)

            elif index_name == "LST":
                # Simplified Brightness Temperature proxy from SWIR band
                # For real Landsat 8/9 TIRS: LST = BT / (1 + (λ·BT/ρ)·ln(ε))
                # Here we approximate from SWIR reflectance to surface temperature (°C)
                # Calibration constants typical for Landsat 8 Band 10
                K1 = 774.89  # W/(m²·sr·µm)
                K2 = 1321.08 # K
                # Use SWIR as a proxy for emitted thermal radiance (scaled 0–1)
                swir = get_band(bands["swir"])
                # Scale reflectance to approximate top-of-atmosphere radiance range
                L_lambda = np.clip(swir, 0.001, 1.0) * 20.0  # W/m²·sr·µm approximation
                # Planck inversion: BT = K2 / ln(K1/L + 1)
                with np.errstate(divide="ignore", invalid="ignore"):
                    bt = np.where(
                        L_lambda > 0,
                        K2 / np.log((K1 / L_lambda) + 1),
                        np.nan
                    )
                # Convert Kelvin → Celsius. Emissivity correction (ε = 0.97 for vegetation)
                epsilon = 0.97
                lst_celsius = bt - 273.15 - (0.00115 * bt ** 2) / epsilon
                index_array = lst_celsius.astype("float32")

            # ── Zonal statistics ─────────────────────────────────────────────
            valid_mask = ~np.isnan(index_array)
            valid_pixels = int(np.sum(valid_mask))
            if valid_pixels > 0:
                mean_val = float(np.nanmean(index_array))
                min_val  = float(np.nanmin(index_array))
                max_val  = float(np.nanmax(index_array))
                std_val  = float(np.nanstd(index_array))
            else:
                mean_val = min_val = max_val = std_val = 0.0

            stats = {
                "mean_value":   mean_val,
                "min_value":    min_val,
                "max_value":    max_val,
                "std_dev":      std_val,
                "valid_pixels": valid_pixels,
            }

            # Fill NaN for storage
            index_array[np.isnan(index_array)] = -9999.0

            # ── Write COG ────────────────────────────────────────────────────
            out_dir  = self.storage_root / "processed"
            out_name = f"processed_{scene.scene_id}_{index_name}.tif"
            out_path = out_dir / out_name

            self._write_cog(src.profile, out_transform, index_array, out_path)

        rel_path = out_path.relative_to(self.storage_root)
        log.info("Index %s computed for scene %s → %s | stats: %s", index_name, scene.scene_id, rel_path, stats)
        return rel_path, stats

    # ── Composite Generation ─────────────────────────────────────────────────

    def generate_composite(
        self,
        scene: SatelliteScene,
        mode: str = "RGB",
        location: Optional[Location] = None,
    ) -> Path:
        """
        Generate a PNG preview composite from satellite bands.
        mode = 'RGB'         → Natural Color  (B4-Red, B3-Green, B2-Blue)
        mode = 'FALSE_COLOR' → Vegetation IR  (B8-NIR, B4-Red, B3-Green)
        mode = 'SWIR'        → Burn Scar/Urban (B11-SWIR, B8-NIR, B4-Red)

        Returns absolute path to the generated PNG file.
        """
        try:
            from PIL import Image
        except ImportError:
            raise RuntimeError("Pillow is required for composite generation. Install it with: pip install Pillow")

        if not scene.file_path:
            raise ValueError(f"Scene {scene.scene_id} has no file_path.")

        file_path = self.storage_root / scene.file_path
        if not file_path.exists():
            raise FileNotFoundError(f"Raster file not found: {file_path}")

        mode = mode.upper()
        if mode not in ("RGB", "FALSE_COLOR", "SWIR"):
            raise ValueError(f"Unsupported composite mode: {mode}. Use RGB, FALSE_COLOR, or SWIR.")

        with rasterio.open(file_path) as src:
            out_image, _ = self._clip_to_location(src, location)
            bands = self._resolve_bands(scene, out_image.shape[0])

            def get_band_arr(idx: int) -> np.ndarray:
                arr = out_image[idx - 1].astype("float32")
                nodata = src.nodata
                if nodata is not None:
                    arr[arr == nodata] = np.nan
                return arr

            # Select band triple based on mode
            if mode == "RGB":
                r = get_band_arr(bands["red"])
                g = get_band_arr(bands["green"])
                b = get_band_arr(bands["blue"])
            elif mode == "FALSE_COLOR":
                r = get_band_arr(bands["nir"])
                g = get_band_arr(bands["red"])
                b = get_band_arr(bands["green"])
            else:  # SWIR
                r = get_band_arr(bands["swir"])
                g = get_band_arr(bands["nir"])
                b = get_band_arr(bands["red"])

        r = np.nan_to_num(r, nan=0.0)
        g = np.nan_to_num(g, nan=0.0)
        b = np.nan_to_num(b, nan=0.0)

        # Joint Spectral Percentile Stretch (preserves natural RGB & False Color ratio)
        p1 = min(np.percentile(r, 1), np.percentile(g, 1), np.percentile(b, 1))
        p99 = max(np.percentile(r, 99), np.percentile(g, 99), np.percentile(b, 99))
        if p99 <= p1:
            p99 = p1 + 0.001

        r_norm = np.clip((r - p1) / (p99 - p1), 0.0, 1.0)
        g_norm = np.clip((g - p1) / (p99 - p1), 0.0, 1.0)
        b_norm = np.clip((b - p1) / (p99 - p1), 0.0, 1.0)

        # Apply mild gamma curve 0.85 for crisp high-contrast visual display
        r8 = (np.power(r_norm, 0.85) * 255).astype(np.uint8)
        g8 = (np.power(g_norm, 0.85) * 255).astype(np.uint8)
        b8 = (np.power(b_norm, 0.85) * 255).astype(np.uint8)

        # Stack to H×W×3 RGB
        rgb = np.dstack([r8, g8, b8])
        img = Image.fromarray(rgb, mode="RGB")

        # Smooth high-quality upscale for preview visibility
        target_size = 512
        resample_filter = getattr(Image, "Resampling", Image).BILINEAR
        img = img.resize((target_size, target_size), resample_filter)

        out_dir = self.storage_root / "composites"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_name = f"composite_{scene.scene_id}_{mode}.png"
        out_path = out_dir / out_name
        img.save(str(out_path), format="PNG")

        log.info("Composite %s generated for scene %s → %s", mode, scene.scene_id, out_path)
        return out_path

    # ── Histogram Computation ────────────────────────────────────────────────

    def compute_histogram(
        self,
        raster_path: Path,
        index_name: str,
        n_bins: int = 32,
    ) -> HistogramResult:
        """
        Compute a statistical histogram of valid pixel values in a processed raster.
        Returns HistogramResult with bin counts, edges and midpoints.
        """
        if not raster_path.exists():
            raise FileNotFoundError(f"Raster file not found: {raster_path}")

        with rasterio.open(raster_path) as src:
            arr = src.read(1).astype("float32")
            nodata = src.nodata if src.nodata is not None else -9999.0
            arr[arr == nodata] = np.nan

        valid = arr[~np.isnan(arr)]
        if len(valid) == 0:
            return HistogramResult([0] * n_bins, list(np.linspace(-1, 1, n_bins + 1)), index_name)

        # Use robust range for LST (°C values instead of -1..+1)
        if index_name == "LST":
            v_min, v_max = float(np.nanmin(valid)), float(np.nanmax(valid))
        else:
            p1, p99 = np.percentile(valid, 1), np.percentile(valid, 99)
            v_min, v_max = float(p1), float(p99)

        if v_min == v_max:
            v_max = v_min + 0.001

        counts, edges = np.histogram(valid, bins=n_bins, range=(v_min, v_max))
        return HistogramResult(counts.tolist(), edges.tolist(), index_name)

    # ── Export Feature ───────────────────────────────────────────────────────

    def export_spatial_features_csv(self, features: list) -> str:
        """
        Convert a list of SpatialFeature ORM objects to CSV string.
        """
        import csv
        import io

        output = io.StringIO()
        fieldnames = [
            "id", "location_id", "index_name",
            "mean_value", "min_value", "max_value", "std_dev",
            "valid_pixels", "created_at"
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for feat in features:
            writer.writerow({
                "id":           feat.id,
                "location_id":  feat.location_id,
                "index_name":   feat.index_name,
                "mean_value":   round(feat.mean_value, 6)   if feat.mean_value   is not None else "",
                "min_value":    round(feat.min_value, 6)    if feat.min_value    is not None else "",
                "max_value":    round(feat.max_value, 6)    if feat.max_value    is not None else "",
                "std_dev":      round(feat.std_dev, 6)      if feat.std_dev      is not None else "",
                "valid_pixels": feat.valid_pixels            if feat.valid_pixels is not None else 0,
                "created_at":   str(feat.created_at),
            })
        return output.getvalue()

    def export_spatial_features_geojson(self, features: list, location) -> Dict[str, Any]:
        """
        Convert SpatialFeature records + location to a GeoJSON FeatureCollection.
        """
        from datetime import datetime

        feature_list = []
        for feat in features:
            feature_list.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [location.longitude, location.latitude],
                },
                "properties": {
                    "id":           feat.id,
                    "location_id":  feat.location_id,
                    "location_name": getattr(location, "name", None),
                    "index_name":   feat.index_name,
                    "mean_value":   feat.mean_value,
                    "min_value":    feat.min_value,
                    "max_value":    feat.max_value,
                    "std_dev":      feat.std_dev      if hasattr(feat, "std_dev")  else None,
                    "valid_pixels": feat.valid_pixels,
                    "created_at":   str(feat.created_at),
                    "crs":          "EPSG:4326",
                },
            })

        return {
            "type": "FeatureCollection",
            "name": f"ClimateX_SpatialFeatures_{location.id}",
            "crs": {
                "type": "name",
                "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
            },
            "generated_at": str(datetime.utcnow()),
            "features": feature_list,
        }


# ─── Singleton accessor ───────────────────────────────────────────────────────

_processor: Optional[EOProcessor] = None


def get_eo_processor() -> EOProcessor:
    global _processor
    if _processor is None:
        _processor = EOProcessor()
    return _processor
