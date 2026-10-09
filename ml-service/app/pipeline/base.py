"""
Pipeline Abstract Base Class — Phase 5B.

Defines the contract every change-detection algorithm must satisfy.
The current implementation (SpectralThresholdDetector) and any future
implementation (RandomForest, UNet, etc.) plug in without touching the
router, schemas, or database layer.

Usage
-----
To add a trained ML model in a future phase:

    class MyMLDetector(ChangeDetectorBase):
        def detect(self, before, after, valid_mask, meta):
            # load model weights, run inference
            ...
            return ChangeResult(...)

    # In pipeline/runner.py, swap the factory:
    def get_detector() -> ChangeDetectorBase:
        return MyMLDetector(...)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np

# Change-map uint8 nodata value for masked pixels (cloud/shadow/out of bounds)
CHANGE_MAP_NODATA: int = 255


@dataclass
class RasterMeta:
    """
    Metadata describing the spatial properties of an aligned raster pair.
    Both rasters must share these properties after the data-loader alignment step.
    """
    crs: str                     # e.g. "EPSG:4326" or "EPSG:32644"
    transform: object            # rasterio Affine transform of the reference raster
    shape: tuple                 # (height, width) in pixels
    resolution_m: float          # Ground sample distance in metres (coarser of the two)
    bounds_wgs84: tuple          # (min_lon, min_lat, max_lon, max_lat) in EPSG:4326
    pixel_area_km2: float        # area of one pixel in km²


@dataclass
class ChangeCategoryStats:
    """Per-category change statistics."""
    category: str                # "vegetation_loss" | "water_gain" | "urban_gain" | ...
    label_value: int             # uint8 value in the change-map raster
    pixel_count: int
    area_km2: float
    description: str


@dataclass
class ChangeResult:
    """
    Output of a change-detection algorithm run.

    Notes
    -----
    * ``change_map`` is a 2-D uint8 numpy array with the same shape as the
      input rasters.  Pixel values:
        0   = no significant change
        1   = water change (gain or loss, see category_stats)
        2   = vegetation change (loss or gain, see category_stats)
        3   = built-up / urban change
        4   = agricultural change (reserved)
        255 = masked (nodata / cloud / shadow in either date)

    * ``signal_quality_index`` is an SNR-based metric [0–1] computed as:
          SQI = clip( mean(|Δ|_changed) / (σ_background + ε), 0, 1 )
      It reflects separation between changed-pixel signal and unchanged-pixel
      noise.  It is NOT a model accuracy or classification confidence score.

    * ``algorithm_name`` / ``algorithm_type`` must never claim "trained model"
      unless the implementation has been trained and validated.
    """
    # ── Change map raster ──────────────────────────────────────────────────────
    change_map: np.ndarray               # uint8, shape = RasterMeta.shape

    # ── Top-level statistics ───────────────────────────────────────────────────
    total_pixels: int
    valid_pixels: int                    # pixels not masked
    changed_pixels: int
    total_area_km2: float
    valid_area_km2: float
    changed_area_km2: float
    changed_pct: float                   # changed_area / valid_area × 100

    # ── Per-category breakdown ─────────────────────────────────────────────────
    category_stats: Dict[str, ChangeCategoryStats] = field(default_factory=dict)

    # ── Signal quality (SNR-based, not model accuracy) ─────────────────────────
    signal_quality_index: float = 0.0   # [0–1]; see docstring above

    # ── Algorithm identity ─────────────────────────────────────────────────────
    algorithm_name: str = ""
    algorithm_version: str = ""
    algorithm_type: str = "threshold_based_spectral_analysis"

    # ── Supplementary metadata ─────────────────────────────────────────────────
    extra_metadata: Dict = field(default_factory=dict)


class ChangeDetectorBase(ABC):
    """
    Abstract base for all change-detection algorithms.

    Parameters
    ----------
    settings : MLSettings
        Service configuration (k_sigma, min_area_px, storage paths …).

    Contract
    --------
    Subclasses implement ``detect()``.  They receive aligned, masked arrays
    and return a ``ChangeResult``.  Input alignment and masking are handled
    *outside* this class by ``data_loader.py``, ensuring every algorithm
    receives consistently prepared data.
    """

    @abstractmethod
    def detect(
        self,
        indices_before: Dict[str, np.ndarray],
        indices_after: Dict[str, np.ndarray],
        valid_mask: np.ndarray,
        meta: RasterMeta,
    ) -> ChangeResult:
        """
        Run change detection.

        Parameters
        ----------
        indices_before : dict
            Mapping of index name → 2-D float32 array for the earlier date.
            Keys are a subset of {"NDVI", "NDWI", "NDBI"}.
            Nodata pixels have already been set to NaN.
        indices_after : dict
            Same structure for the later date.
        valid_mask : np.ndarray, bool
            True where *both* dates have valid (non-NaN) data for *all* indices.
            The detector must restrict all computations to these pixels.
        meta : RasterMeta
            Spatial metadata describing both rasters (identical after alignment).

        Returns
        -------
        ChangeResult
        """
        ...
