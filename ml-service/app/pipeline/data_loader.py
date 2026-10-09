"""
Data Loader for Change Detection — Phase 5B.

Responsibilities
----------------
1. Locate Phase 5A processed COG GeoTIFFs for two satellite scenes.
2. Load and align them spatially:
   - Reproject secondary raster to reference CRS if they differ.
   - Resample to the coarser pixel spacing to avoid sub-pixel artefacts.
   - Clip both to their spatial intersection (raises ValueError if empty).
3. Build and return a combined nodata / cloud / shadow mask.
4. Return aligned float32 arrays and spatial metadata.

Alignment decisions are recorded in the ``alignment_provenance`` dict,
which is stored verbatim in ``MLResult.provenance`` for auditability.

Nodata convention (from Phase 5A)
----------------------------------
Phase 5A writes nodata = -9999.0 (float32).  Any pixel where *either* date
has value ≤ -9998.0 is excluded from analysis.  The valid mask is:
    valid_mask = (arr_before > -9998.0) & (arr_after > -9998.0)

This implicitly excludes cloud, shadow, and out-of-bounds pixels that were
set to nodata during Phase 5A processing.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import array_bounds
from rasterio.warp import (
    calculate_default_transform,
    reproject as rasterio_reproject,
    Resampling,
)

from .base import RasterMeta

log = logging.getLogger(__name__)

# Phase 5A nodata sentinel value
NODATA_VALUE: float = -9999.0
# Pixels at or below this threshold are considered masked
NODATA_THRESHOLD: float = -9998.0

# Supported spectral indices for change detection
SUPPORTED_INDICES: List[str] = ["NDVI", "NDWI", "NDBI"]

# Change-map nodata pixel value (uint8)
CHANGE_MAP_NODATA: int = 255


class AlignmentError(Exception):
    """Raised when the two rasters cannot be aligned (e.g., no spatial overlap)."""


def _load_single_band(path: Path) -> Tuple[np.ndarray, rasterio.DatasetReader]:
    """
    Open a single-band COG GeoTIFF and return (float32 array, open dataset).
    The dataset is returned open so the caller can read CRS/transform.
    The array uses NaN for nodata pixels (nodata = NODATA_VALUE).
    """
    src = rasterio.open(path)
    arr = src.read(1).astype("float32")
    # Replace Phase 5A sentinel with NaN for safe arithmetic
    arr[arr <= NODATA_THRESHOLD] = np.nan
    return arr, src


def _reproject_to_reference(
    src_arr: np.ndarray,
    src_dataset: rasterio.DatasetReader,
    ref_crs: CRS,
    ref_transform,
    ref_shape: Tuple[int, int],
) -> np.ndarray:
    """
    Reproject and resample ``src_arr`` so it aligns with the reference raster.
    Returns a float32 array of shape ``ref_shape`` with NaN for nodata.
    """
    dst_arr = np.full(ref_shape, np.nan, dtype="float32")

    # Replace NaN with a float nodata value rasterio can work with
    src_with_nodata = np.where(np.isnan(src_arr), NODATA_VALUE, src_arr).astype("float32")

    rasterio_reproject(
        source=src_with_nodata,
        destination=dst_arr,
        src_transform=src_dataset.transform,
        src_crs=src_dataset.crs,
        src_nodata=NODATA_VALUE,
        dst_transform=ref_transform,
        dst_crs=ref_crs,
        dst_nodata=np.nan,
        resampling=Resampling.bilinear,
    )
    return dst_arr


def _compute_intersection_bounds(
    bounds_a, crs_a: CRS, bounds_b, crs_b: CRS
) -> Optional[Tuple[float, float, float, float]]:
    """
    Compute the intersection of two bounding boxes both reprojected to EPSG:4326.
    Returns (left, bottom, right, top) or None if no overlap.
    """
    from rasterio.warp import transform_bounds

    target_crs = CRS.from_epsg(4326)

    def to_wgs84(bounds, crs):
        if crs == target_crs:
            return bounds
        return transform_bounds(crs, target_crs, *bounds)

    b_a = to_wgs84(bounds_a, crs_a)
    b_b = to_wgs84(bounds_b, crs_b)

    left = max(b_a[0], b_b[0])
    bottom = max(b_a[1], b_b[1])
    right = min(b_a[2], b_b[2])
    top = min(b_a[3], b_b[3])

    if left >= right or bottom >= top:
        return None
    return (left, bottom, right, top)


def load_aligned_index_pair(
    eo_storage_root: Path,
    before_raster_path: str,
    after_raster_path: str,
    index_name: str,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, RasterMeta, dict]:
    """
    Load a before/after pair of Phase 5A index rasters and align them.

    Parameters
    ----------
    eo_storage_root : Path
        Root of the Phase 5A storage tree (EO_STORAGE_PATH).
    before_raster_path : str
        Path to the "before" COG relative to eo_storage_root.
    after_raster_path : str
        Path to the "after" COG relative to eo_storage_root.
    index_name : str
        Index being loaded (e.g. "NDVI") — used only for logging.

    Returns
    -------
    arr_before : np.ndarray  float32, NaN where nodata
    arr_after  : np.ndarray  float32, NaN where nodata, aligned to arr_before
    valid_mask : np.ndarray  bool, True where both dates are valid
    meta       : RasterMeta  spatial metadata of the aligned pair
    provenance : dict        alignment audit record for storage in MLResult
    """
    before_path = eo_storage_root / before_raster_path
    after_path = eo_storage_root / after_raster_path

    if not before_path.exists():
        raise FileNotFoundError(f"Before raster not found: {before_path}")
    if not after_path.exists():
        raise FileNotFoundError(f"After raster not found: {after_path}")

    log.info("[%s] Loading before: %s", index_name, before_path)
    arr_before, src_before = _load_single_band(before_path)

    log.info("[%s] Loading after:  %s", index_name, after_path)
    arr_after, src_after = _load_single_band(after_path)

    ref_crs = src_before.crs
    ref_transform = src_before.transform
    ref_shape = (src_before.height, src_before.width)

    reprojected = False
    resampled = False
    ref_res = abs(src_before.transform.a)    # pixel width in CRS units
    sec_res = abs(src_after.transform.a)

    # ── Step 1: Reproject if CRS differs ────────────────────────────────────
    if src_after.crs != ref_crs:
        log.info(
            "[%s] CRS mismatch (%s vs %s) — reprojecting secondary to reference CRS.",
            index_name, src_after.crs, ref_crs
        )
        arr_after = _reproject_to_reference(
            arr_after, src_after, ref_crs, ref_transform, ref_shape
        )
        reprojected = True

    # ── Step 2: Resample if pixel spacing differs significantly (>10%) ───────
    elif abs(ref_res - sec_res) / max(ref_res, sec_res) > 0.10:
        log.info(
            "[%s] Resolution mismatch (%.1f m vs %.1f m) — resampling to coarser.",
            index_name, ref_res * 111_000, sec_res * 111_000
        )
        # Choose coarser resolution as output to avoid spurious detail
        if sec_res > ref_res:
            # Reference is finer; reproject before-raster to secondary's resolution
            new_transform, new_w, new_h = calculate_default_transform(
                ref_crs, ref_crs,
                src_after.width, src_after.height,
                *src_after.bounds,
            )
            tmp = np.full((new_h, new_w), np.nan, dtype="float32")
            src_before_nodata = np.where(np.isnan(arr_before), NODATA_VALUE, arr_before)
            rasterio_reproject(
                source=src_before_nodata,
                destination=tmp,
                src_transform=ref_transform,
                src_crs=ref_crs,
                src_nodata=NODATA_VALUE,
                dst_transform=new_transform,
                dst_crs=ref_crs,
                dst_nodata=np.nan,
                resampling=Resampling.bilinear,
            )
            arr_before = tmp
            ref_transform = new_transform
            ref_shape = (new_h, new_w)
            ref_res = sec_res
        else:
            # Secondary is finer; resample it to match reference
            arr_after = _reproject_to_reference(
                arr_after, src_after, ref_crs, ref_transform, ref_shape
            )
        resampled = True

    elif arr_before.shape != arr_after.shape:
        # Same CRS and similar resolution but different shape — force-align
        log.info(
            "[%s] Shape mismatch (%s vs %s) — reprojecting to reference grid.",
            index_name, arr_before.shape, arr_after.shape
        )
        arr_after = _reproject_to_reference(
            arr_after, src_after, ref_crs, ref_transform, ref_shape
        )
        reprojected = True

    # ── Step 3: Verify shapes match ─────────────────────────────────────────
    if arr_before.shape != arr_after.shape:
        raise AlignmentError(
            f"Shape mismatch after alignment: {arr_before.shape} vs {arr_after.shape}"
        )

    # ── Step 4: Check spatial overlap ────────────────────────────────────────
    intersection = _compute_intersection_bounds(
        src_before.bounds, src_before.crs,
        src_after.bounds, src_after.crs,
    )
    if intersection is None:
        raise AlignmentError(
            "Before and after rasters have no spatial overlap. "
            "Ensure both scenes cover the same Area of Interest."
        )

    # ── Step 5: Combined valid mask (nodata in either date → masked) ─────────
    valid_mask = (~np.isnan(arr_before)) & (~np.isnan(arr_after))
    total_px = arr_before.size
    valid_px = int(np.sum(valid_mask))
    valid_fraction = valid_px / total_px if total_px > 0 else 0.0

    log.info(
        "[%s] Alignment complete. Shape=%s valid=%.1f%% reprojected=%s resampled=%s",
        index_name, arr_before.shape, valid_fraction * 100, reprojected, resampled
    )

    # ── Compute resolution in metres (approximate for geographic CRS) ────────
    if ref_crs.is_geographic:
        # 1 degree latitude ≈ 111 km; use pixel width in degrees × 111 000
        resolution_m = abs(ref_transform.a) * 111_000
    else:
        resolution_m = abs(ref_transform.a)  # CRS units are already metres

    pixel_area_km2 = (resolution_m / 1000) ** 2

    # ── Build RasterMeta ─────────────────────────────────────────────────────
    h, w = arr_before.shape
    bounds_wgs84 = intersection  # already in WGS84

    meta = RasterMeta(
        crs=str(ref_crs),
        transform=ref_transform,
        shape=(h, w),
        resolution_m=round(resolution_m, 1),
        bounds_wgs84=bounds_wgs84,
        pixel_area_km2=pixel_area_km2,
    )

    # ── Alignment provenance ─────────────────────────────────────────────────
    provenance = {
        "reference_raster": "before",
        "reprojected": reprojected,
        "resampled": resampled,
        "resampled_to_m": round(resolution_m, 1),
        "output_crs": str(ref_crs),
        "output_shape": list(arr_before.shape),
        "extent_intersection_wgs84": list(intersection),
        "nodata_threshold": NODATA_THRESHOLD,
        "valid_pixel_fraction": round(valid_fraction, 4),
        "total_pixels": total_px,
        "valid_pixels": valid_px,
    }

    src_before.close()
    src_after.close()

    return arr_before, arr_after, valid_mask, meta, provenance


def load_multi_index_pairs(
    eo_storage_root: Path,
    before_raster_paths: Dict[str, str],
    after_raster_paths: Dict[str, str],
) -> Tuple[
    Dict[str, np.ndarray],
    Dict[str, np.ndarray],
    np.ndarray,
    RasterMeta,
    Dict[str, dict],
]:
    """
    Load and align multiple index pairs (NDVI, NDWI, NDBI) simultaneously.

    The valid mask is the intersection of all per-index masks:
    a pixel must be valid in ALL indices in BOTH dates to be analysed.

    Returns
    -------
    before_arrs   : {index_name: aligned float32 array}
    after_arrs    : {index_name: aligned float32 array}
    combined_mask : bool array; True = valid in all indices & both dates
    meta          : spatial metadata (from first successfully loaded pair)
    provenances   : {index_name: alignment_provenance_dict}
    """
    before_arrs: Dict[str, np.ndarray] = {}
    after_arrs: Dict[str, np.ndarray] = {}
    provenances: Dict[str, dict] = {}
    combined_mask: Optional[np.ndarray] = None
    shared_meta: Optional[RasterMeta] = None

    for index_name in SUPPORTED_INDICES:
        if index_name not in before_raster_paths or index_name not in after_raster_paths:
            log.debug("Index %s not available — skipping.", index_name)
            continue

        arr_b, arr_a, valid, meta, prov = load_aligned_index_pair(
            eo_storage_root,
            before_raster_paths[index_name],
            after_raster_paths[index_name],
            index_name,
        )

        before_arrs[index_name] = arr_b
        after_arrs[index_name] = arr_a
        provenances[index_name] = prov

        if combined_mask is None:
            combined_mask = valid
            shared_meta = meta
        else:
            # Intersect masks — align shapes if needed
            if valid.shape != combined_mask.shape:
                log.warning(
                    "Mask shape mismatch across indices (%s vs %s). "
                    "Using first index shape as reference.",
                    valid.shape, combined_mask.shape
                )
                # Truncate to common size (conservative)
                min_h = min(valid.shape[0], combined_mask.shape[0])
                min_w = min(valid.shape[1], combined_mask.shape[1])
                combined_mask = combined_mask[:min_h, :min_w] & valid[:min_h, :min_w]
                for k in before_arrs:
                    before_arrs[k] = before_arrs[k][:min_h, :min_w]
                    after_arrs[k] = after_arrs[k][:min_h, :min_w]
            else:
                combined_mask = combined_mask & valid

    if combined_mask is None:
        raise ValueError("No supported index rasters could be loaded for either date.")

    # Update combined valid fraction in each provenance record
    valid_px = int(np.sum(combined_mask))
    total_px = combined_mask.size
    for prov in provenances.values():
        prov["combined_valid_pixels"] = valid_px
        prov["combined_total_pixels"] = total_px
        prov["combined_valid_fraction"] = round(valid_px / total_px, 4) if total_px else 0.0

    return before_arrs, after_arrs, combined_mask, shared_meta, provenances
