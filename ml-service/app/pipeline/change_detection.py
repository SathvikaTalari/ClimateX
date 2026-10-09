"""
Multi-Index Spectral Change Detection (MISCD) — Phase 5B.

Algorithm
---------
Algorithm name    : Multi-Index Spectral Change Detection (MISCD)
Algorithm version : 1.0.0
Algorithm type    : threshold_based_spectral_analysis

This is a classical, unsupervised remote-sensing change-detection algorithm.
It is NOT a trained machine-learning model and makes no accuracy claims.

Method
------
For each spectral index (NDVI, NDWI, NDBI):
  1. Compute the per-pixel difference: Δ = after − before.
  2. Compute μ and σ of Δ on valid (unmasked) pixels only.
  3. Pixels where |Δ| > k·σ are flagged as "significantly changed".
     k = k_sigma (default 1.5) — a sensitivity parameter, not a trained weight.

Category assignment (hierarchical, first-match wins):
  • NDWI gain  (Δndwi >  k·σ_ndwi) → water_gain
  • NDWI loss  (Δndwi < -k·σ_ndwi) → water_loss
  • NDVI loss  (Δndvi < -k·σ_ndvi) → vegetation_loss
  • NDVI gain  (Δndvi >  k·σ_ndvi) → vegetation_gain
  • NDBI gain  (Δndbi >  k·σ_ndbi) → urban_gain
  • NDBI loss  (Δndbi < -k·σ_ndbi) → urban_loss

Noise suppression
-----------------
After classification, connected components with fewer than
``min_change_area_px`` pixels are removed (binary morphological opening
with a 3×3 square structuring element). This suppresses salt-and-pepper
noise caused by atmospheric effects or individual outlier pixels.

Signal Quality Index (SQI)
--------------------------
SQI = clip( mean(|Δ|_changed) / (σ_background + ε), 0, 1 )

Where:
  • |Δ|_changed  = mean absolute difference of changed pixels
  • σ_background = standard deviation of |Δ| on unchanged valid pixels
  • ε = 0.01 (numerical stability)

SQI measures how clearly detected changes stand out above background
variation.  It is NOT a model accuracy or classification confidence score.
A score close to 1 means the detected changes are large relative to the
noise floor; close to 0 means the signal barely exceeds noise.

References
----------
Lu, D., Mausel, P., Brondízio, E., & Moran, E. (2004).
Change detection techniques. International Journal of Remote Sensing, 25(12).
"""
from __future__ import annotations

import logging
from typing import Dict, Optional

import numpy as np
from scipy.ndimage import label as ndimage_label

from .base import (
    ChangeDetectorBase,
    ChangeCategoryStats,
    ChangeResult,
    RasterMeta,
    CHANGE_MAP_NODATA,
)

log = logging.getLogger(__name__)

# ── Change map pixel labels ────────────────────────────────────────────────────
LABEL_NO_CHANGE = 0
LABEL_WATER = 1
LABEL_VEGETATION = 2
LABEL_URBAN = 3
LABEL_AGRICULTURE = 4  # reserved for future use

# ── Category metadata (for UI rendering and provenance) ───────────────────────
CATEGORY_META: Dict[int, Dict] = {
    LABEL_WATER: {
        "name": "water_change",
        "display": "Water Body Change",
        "color_hex": "#2196F3",
    },
    LABEL_VEGETATION: {
        "name": "vegetation_change",
        "display": "Vegetation / Forest Change",
        "color_hex": "#4CAF50",
    },
    LABEL_URBAN: {
        "name": "urban_change",
        "display": "Built-up / Urban Change",
        "color_hex": "#FF5722",
    },
    LABEL_AGRICULTURE: {
        "name": "agricultural_change",
        "display": "Agricultural Change",
        "color_hex": "#FFC107",
    },
}


class SpectralThresholdDetector(ChangeDetectorBase):
    """
    MISCD v1.0.0 — Multi-Index Spectral Change Detection.

    Parameters
    ----------
    k_sigma : float
        Threshold multiplier. Changed pixels satisfy |Δ| > k_sigma × σ.
        Default 1.5 gives a reasonable balance between sensitivity and
        false-positive rate for Sentinel-2 imagery.
    min_change_area_px : int
        Minimum connected-component size (pixels) to keep.
        Smaller components are removed as speckle noise.
    """

    ALGORITHM_NAME = "MISCD"
    ALGORITHM_VERSION = "1.0.0"
    ALGORITHM_TYPE = "threshold_based_spectral_analysis"

    def __init__(self, k_sigma: float = 1.5, min_change_area_px: int = 9):
        self.k_sigma = k_sigma
        self.min_change_area_px = min_change_area_px

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _compute_delta(
        self,
        before: np.ndarray,
        after: np.ndarray,
        valid_mask: np.ndarray,
    ) -> Dict[str, float]:
        """
        Compute per-index difference statistics on valid pixels only.
        Returns {delta, mu, sigma, threshold}.
        """
        delta = np.where(valid_mask, after - before, np.nan)
        valid_delta = delta[valid_mask]
        mu = float(np.nanmean(valid_delta)) if len(valid_delta) else 0.0
        sigma = float(np.nanstd(valid_delta)) if len(valid_delta) else 0.0
        threshold = self.k_sigma * sigma
        return {"delta": delta, "mu": mu, "sigma": sigma, "threshold": threshold}

    def _remove_small_components(
        self, binary_mask: np.ndarray, min_px: int
    ) -> np.ndarray:
        """
        Remove connected components with fewer than ``min_px`` pixels.
        Uses 8-connectivity (diagonal neighbours count).
        """
        if min_px <= 1:
            return binary_mask
        structure = np.ones((3, 3), dtype=int)  # 8-connectivity
        labeled, _ = ndimage_label(binary_mask, structure=structure)
        component_sizes = np.bincount(labeled.ravel())
        # Keep components large enough (component 0 = background, always excluded)
        component_sizes[0] = 0
        keep = component_sizes >= min_px
        cleaned = keep[labeled]
        return cleaned.astype(bool)

    def _signal_quality_index(
        self,
        delta_arrays: Dict[str, np.ndarray],
        change_mask: np.ndarray,
        valid_mask: np.ndarray,
    ) -> float:
        """
        Compute the Signal Quality Index (SQI) across all available indices.

        SQI = clip( mean(|Δ|_changed) / (σ_background + ε), 0, 1 )

        This is an SNR-based metric, not a model accuracy or confidence score.
        """
        eps = 0.01
        signal_values = []
        noise_sigmas = []

        unchanged_mask = valid_mask & ~change_mask

        for delta in delta_arrays.values():
            abs_delta = np.abs(delta)

            # Signal: mean absolute change on changed pixels
            changed_vals = abs_delta[change_mask & valid_mask]
            if len(changed_vals) > 0:
                signal_values.append(float(np.mean(changed_vals)))

            # Noise floor: std of absolute change on unchanged pixels
            unchanged_vals = abs_delta[unchanged_mask]
            if len(unchanged_vals) > 1:
                noise_sigmas.append(float(np.std(unchanged_vals)))

        if not signal_values or not noise_sigmas:
            return 0.0

        mean_signal = float(np.mean(signal_values))
        mean_noise = float(np.mean(noise_sigmas))

        sqi = float(np.clip(mean_signal / (mean_noise + eps), 0.0, 1.0))
        return round(sqi, 4)

    # ── Main detection method ─────────────────────────────────────────────────

    def detect(
        self,
        indices_before: Dict[str, np.ndarray],
        indices_after: Dict[str, np.ndarray],
        valid_mask: np.ndarray,
        meta: RasterMeta,
    ) -> ChangeResult:
        """
        Run MISCD change detection on aligned, masked index rasters.

        See module docstring for algorithm details.
        """
        h, w = meta.shape
        log.info(
            "MISCD v%s: shape=%s k_sigma=%.2f min_area_px=%d available_indices=%s",
            self.ALGORITHM_VERSION, meta.shape, self.k_sigma,
            self.min_change_area_px, list(indices_before.keys()),
        )

        # ── Compute per-index deltas ──────────────────────────────────────────
        deltas: Dict[str, dict] = {}
        for idx_name in indices_before:
            if idx_name in indices_after:
                deltas[idx_name] = self._compute_delta(
                    indices_before[idx_name],
                    indices_after[idx_name],
                    valid_mask,
                )
                log.debug(
                    "[%s] Δμ=%.4f Δσ=%.4f threshold=%.4f",
                    idx_name,
                    deltas[idx_name]["mu"],
                    deltas[idx_name]["sigma"],
                    deltas[idx_name]["threshold"],
                )

        if not deltas:
            raise ValueError(
                "No matching before/after index pairs found. "
                "Ensure Phase 5A processing completed for both scenes."
            )

        # ── Initialise change map ─────────────────────────────────────────────
        # 255 = NODATA (masked), 0 = no change, 1/2/3 = categories
        change_map = np.full((h, w), CHANGE_MAP_NODATA, dtype=np.uint8)
        change_map[valid_mask] = LABEL_NO_CHANGE

        # ── Category assignment (hierarchical, first-match wins) ──────────────
        #
        # Priority: Water > Vegetation > Urban
        # Rationale: NDWI is most spectrally distinct; NDBI is noisiest.
        # Where multiple indices flag the same pixel, water and vegetation
        # changes are ecologically more significant than built-up changes.

        # Water change (NDWI)
        if "NDWI" in deltas:
            d = deltas["NDWI"]
            delta_ndwi = d["delta"]
            thr = d["threshold"]
            water_changed = valid_mask & (np.abs(delta_ndwi) > thr)
            water_changed = self._remove_small_components(water_changed, self.min_change_area_px)
            change_map[water_changed] = LABEL_WATER
            log.debug("Water pixels flagged: %d", int(np.sum(water_changed)))

        # Vegetation change (NDVI) — only on pixels not already labelled
        if "NDVI" in deltas:
            d = deltas["NDVI"]
            delta_ndvi = d["delta"]
            thr = d["threshold"]
            unlabelled = valid_mask & (change_map == LABEL_NO_CHANGE)
            veg_changed = unlabelled & (np.abs(delta_ndvi) > thr)
            veg_changed = self._remove_small_components(veg_changed, self.min_change_area_px)
            change_map[veg_changed] = LABEL_VEGETATION
            log.debug("Vegetation pixels flagged: %d", int(np.sum(veg_changed)))

        # Urban change (NDBI) — only on pixels not already labelled
        if "NDBI" in deltas:
            d = deltas["NDBI"]
            delta_ndbi = d["delta"]
            thr = d["threshold"]
            unlabelled = valid_mask & (change_map == LABEL_NO_CHANGE)
            urban_changed = unlabelled & (np.abs(delta_ndbi) > thr)
            urban_changed = self._remove_small_components(urban_changed, self.min_change_area_px)
            change_map[urban_changed] = LABEL_URBAN
            log.debug("Urban pixels flagged: %d", int(np.sum(urban_changed)))

        # ── Compute statistics ────────────────────────────────────────────────
        total_px = valid_mask.size
        valid_px = int(np.sum(valid_mask))
        changed_mask = valid_mask & (change_map > LABEL_NO_CHANGE) & (change_map < CHANGE_MAP_NODATA)
        changed_px = int(np.sum(changed_mask))

        total_area_km2 = round(total_px * meta.pixel_area_km2, 4)
        valid_area_km2 = round(valid_px * meta.pixel_area_km2, 4)
        changed_area_km2 = round(changed_px * meta.pixel_area_km2, 4)
        changed_pct = (
            round((changed_px / valid_px) * 100, 4) if valid_px > 0 else 0.0
        )

        # ── Per-category statistics ───────────────────────────────────────────
        category_stats: Dict[str, ChangeCategoryStats] = {}
        for label_val, cat_meta in CATEGORY_META.items():
            px_count = int(np.sum(change_map == label_val))
            if px_count == 0:
                continue

            # Determine direction from dominant delta sign
            category_name = cat_meta["name"]
            if label_val == LABEL_WATER and "NDWI" in deltas:
                delta_arr = deltas["NDWI"]["delta"]
                cat_pixels = (change_map == LABEL_WATER) & valid_mask
                mean_delta = float(np.nanmean(delta_arr[cat_pixels])) if np.any(cat_pixels) else 0
                category_name = "water_gain" if mean_delta > 0 else "water_loss"
                desc = "Water body expansion" if mean_delta > 0 else "Water body contraction / drying"
            elif label_val == LABEL_VEGETATION and "NDVI" in deltas:
                delta_arr = deltas["NDVI"]["delta"]
                cat_pixels = (change_map == LABEL_VEGETATION) & valid_mask
                mean_delta = float(np.nanmean(delta_arr[cat_pixels])) if np.any(cat_pixels) else 0
                category_name = "vegetation_gain" if mean_delta > 0 else "vegetation_loss"
                desc = "Vegetation / canopy gain" if mean_delta > 0 else "Vegetation / deforestation loss"
            elif label_val == LABEL_URBAN and "NDBI" in deltas:
                delta_arr = deltas["NDBI"]["delta"]
                cat_pixels = (change_map == LABEL_URBAN) & valid_mask
                mean_delta = float(np.nanmean(delta_arr[cat_pixels])) if np.any(cat_pixels) else 0
                category_name = "urban_gain" if mean_delta > 0 else "urban_loss"
                desc = "New built-up / urban expansion" if mean_delta > 0 else "Urban reduction / demolition"
            else:
                desc = cat_meta["display"]

            category_stats[category_name] = ChangeCategoryStats(
                category=category_name,
                label_value=label_val,
                pixel_count=px_count,
                area_km2=round(px_count * meta.pixel_area_km2, 4),
                description=desc,
            )

        # ── Signal Quality Index ──────────────────────────────────────────────
        delta_arrays_only = {k: v["delta"] for k, v in deltas.items()}
        sqi = self._signal_quality_index(delta_arrays_only, changed_mask, valid_mask)
        log.info(
            "MISCD complete. changed_pct=%.2f%% changed_km2=%.2f SQI=%.3f",
            changed_pct, changed_area_km2, sqi,
        )

        # ── Threshold provenance ──────────────────────────────────────────────
        threshold_metadata = {
            idx: {
                "mu": round(d["mu"], 6),
                "sigma": round(d["sigma"], 6),
                "k_sigma": self.k_sigma,
                "threshold": round(d["threshold"], 6),
            }
            for idx, d in deltas.items()
        }

        return ChangeResult(
            change_map=change_map,
            total_pixels=total_px,
            valid_pixels=valid_px,
            changed_pixels=changed_px,
            total_area_km2=total_area_km2,
            valid_area_km2=valid_area_km2,
            changed_area_km2=changed_area_km2,
            changed_pct=changed_pct,
            category_stats=category_stats,
            signal_quality_index=sqi,
            algorithm_name=self.ALGORITHM_NAME,
            algorithm_version=self.ALGORITHM_VERSION,
            algorithm_type=self.ALGORITHM_TYPE,
            extra_metadata={
                "thresholds": threshold_metadata,
                "min_change_area_px": self.min_change_area_px,
                "indices_used": list(deltas.keys()),
                "category_color_map": {
                    v["name"]: v["color_hex"] for v in CATEGORY_META.values()
                },
            },
        )
