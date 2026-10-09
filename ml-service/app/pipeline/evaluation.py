"""
Change-Detection Evaluation Metrics — Phase 5B.

Computes pixel-level binary classification metrics against a labelled
ground-truth mask.  Used both offline (benchmarking on OSCD/LEVIR-CD) and
online (if a user supplies a reference mask via the API).

When NO ground truth is available (the normal production case today) every
function returns ``None`` and the API records ``evaluation_metrics: null``.
This is the honest answer — the service makes no accuracy claims it cannot
support.

Metrics
-------
All metrics are computed pixel-by-pixel on the binary ``changed / unchanged``
classification (changed = label > 0; unchanged = label == 0; NODATA is excluded).

  Precision = TP / (TP + FP)
  Recall    = TP / (TP + FN)   (also called Sensitivity / TPR)
  F1        = 2 × P × R / (P + R)
  IoU       = TP / (TP + FP + FN)   (Jaccard index)
  Accuracy  = (TP + TN) / (TP + TN + FP + FN)

Confusion matrix is returned as a plain dict with keys TP, TN, FP, FN to
make JSON serialisation straightforward.

References
----------
Daudt, R. C., Le Saux, B., & Boulch, A. (2018).
Fully Convolutional Siamese Networks for Change Detection.
ICIP 2018. https://arxiv.org/abs/1810.08462  (OSCD baseline metrics)

Chen, H., et al. (2021).
Remote Sensing Image Change Detection with Transformers.
IEEE TGRS. https://arxiv.org/abs/2103.00208  (TransUNet-CD metrics)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional

import numpy as np

from .base import CHANGE_MAP_NODATA

log = logging.getLogger(__name__)

# Binary change label used for evaluation (any non-zero, non-nodata pixel)
_CHANGED_LABEL_THRESHOLD = 0


@dataclass
class EvaluationMetrics:
    """
    Pixel-level binary change-detection evaluation metrics.

    All float values are in [0, 1] (except where noted).
    Values are ``None`` when the metric cannot be computed (e.g., zero
    denominator — meaning there were no positive predictions or no actual
    positives in the evaluation area).
    """
    # ── Core metrics ───────────────────────────────────────────────────────────
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    iou: Optional[float] = None           # Intersection over Union (Jaccard)
    accuracy: Optional[float] = None

    # ── Confusion matrix components ────────────────────────────────────────────
    true_positives: int = 0
    true_negatives: int = 0
    false_positives: int = 0
    false_negatives: int = 0

    # ── Coverage ──────────────────────────────────────────────────────────────
    evaluated_pixels: int = 0            # pixels in both pred and GT (excl. nodata)
    changed_in_gt: int = 0              # positives in the ground-truth mask
    changed_in_pred: int = 0            # positives in the prediction

    # ── Provenance ─────────────────────────────────────────────────────────────
    ground_truth_source: str = ""        # dataset name or file path
    notes: str = ""

    def to_dict(self) -> Dict:
        """Return a plain dict suitable for JSON serialisation."""
        return {k: v for k, v in asdict(self).items()}


class ChangeDetectionEvaluator:
    """
    Evaluates a change-detection prediction mask against a ground-truth mask.

    Usage
    -----
    ::

        evaluator = ChangeDetectionEvaluator()
        metrics = evaluator.compute(pred_mask, gt_mask, gt_source="LEVIR-CD")

    Both masks must be 2-D numpy arrays of the same shape.  Pixel conventions:

    Prediction mask (``pred_mask``)
        uint8 array produced by ``SpectralThresholdDetector.detect()``.
        0 = no change; 1/2/3 = change categories; 255 = nodata.

    Ground-truth mask (``gt_mask``)
        Binary uint8 array where:
        1 = changed, 0 = unchanged, 255 = nodata/ignore.
        (LEVIR-CD and OSCD both use this convention.)
    """

    NODATA = CHANGE_MAP_NODATA  # 255

    def compute(
        self,
        pred_mask: np.ndarray,
        gt_mask: np.ndarray,
        gt_source: str = "unknown",
        notes: str = "",
    ) -> EvaluationMetrics:
        """
        Compute all evaluation metrics.

        Parameters
        ----------
        pred_mask : np.ndarray
            Uint8 change-category map from the detector (0=no change, 1-4=change, 255=nodata).
        gt_mask : np.ndarray
            Binary ground-truth mask (0=unchanged, 1=changed, 255=nodata/ignore).
        gt_source : str
            Human-readable description of the ground-truth dataset (e.g., "LEVIR-CD").
        notes : str
            Any additional notes to store in provenance.

        Returns
        -------
        EvaluationMetrics
        """
        if pred_mask.shape != gt_mask.shape:
            raise ValueError(
                f"Shape mismatch: prediction {pred_mask.shape} vs "
                f"ground truth {gt_mask.shape}. Both masks must be aligned."
            )

        # ── Build evaluation mask (exclude nodata in either mask) ────────────
        valid = (pred_mask != self.NODATA) & (gt_mask != self.NODATA)
        n_valid = int(np.sum(valid))

        if n_valid == 0:
            log.warning("No valid pixels to evaluate (all masked as nodata).")
            return EvaluationMetrics(
                evaluated_pixels=0,
                ground_truth_source=gt_source,
                notes="No valid pixels — all masked as nodata in pred or GT.",
            )

        # ── Binarise ──────────────────────────────────────────────────────────
        # Prediction: any label > 0 (and not nodata) → changed
        pred_bin = (pred_mask > _CHANGED_LABEL_THRESHOLD) & valid
        # Ground truth: label == 1 → changed
        gt_bin = (gt_mask == 1) & valid

        # ── Confusion matrix ──────────────────────────────────────────────────
        tp = int(np.sum(pred_bin & gt_bin))
        tn = int(np.sum(~pred_bin & ~gt_bin & valid))
        fp = int(np.sum(pred_bin & ~gt_bin))
        fn = int(np.sum(~pred_bin & gt_bin))

        log.info(
            "Evaluation — TP=%d TN=%d FP=%d FN=%d (n_valid=%d)",
            tp, tn, fp, fn, n_valid,
        )

        # ── Metrics ──────────────────────────────────────────────────────────
        precision = self._safe_divide(tp, tp + fp)
        recall    = self._safe_divide(tp, tp + fn)
        f1        = self._safe_divide(2 * tp, 2 * tp + fp + fn)
        iou       = self._safe_divide(tp, tp + fp + fn)
        accuracy  = self._safe_divide(tp + tn, n_valid)

        return EvaluationMetrics(
            precision=precision,
            recall=recall,
            f1_score=f1,
            iou=iou,
            accuracy=accuracy,
            true_positives=tp,
            true_negatives=tn,
            false_positives=fp,
            false_negatives=fn,
            evaluated_pixels=n_valid,
            changed_in_gt=int(np.sum(gt_bin)),
            changed_in_pred=int(np.sum(pred_bin)),
            ground_truth_source=gt_source,
            notes=notes,
        )

    @staticmethod
    def _safe_divide(numerator: int, denominator: int) -> Optional[float]:
        """Return ``None`` instead of dividing by zero."""
        if denominator == 0:
            return None
        return round(numerator / denominator, 6)
