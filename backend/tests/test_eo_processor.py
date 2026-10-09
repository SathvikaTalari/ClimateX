import pytest
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.services.eo_processor import EOProcessor
from app.models.satellite import SatelliteScene
from app.models.location import Location


def test_eo_processor_missing_file():
    processor = EOProcessor()
    scene = SatelliteScene(
        scene_id="S2A_TEST_MISSING",
        file_path="non_existent_file.tif",
        sensor="MSI",
    )
    with pytest.raises(FileNotFoundError):
        processor.process_index(scene, "NDVI")


def test_eo_processor_calculation(tmp_path):
    import rasterio
    from rasterio.transform import from_origin

    test_file = tmp_path / "test_scene.tif"
    transform = from_origin(78.80, 16.40, 0.001, 0.001)
    profile = {
        "driver": "GTiff",
        "height": 50,
        "width": 50,
        "count": 5,
        "dtype": "float32",
        "crs": "EPSG:4326",
        "transform": transform,
    }
    b2 = np.full((50, 50), 0.05, dtype="float32")
    b3 = np.full((50, 50), 0.08, dtype="float32")
    b4 = np.full((50, 50), 0.10, dtype="float32")  # Red = 0.10
    b8 = np.full((50, 50), 0.50, dtype="float32")  # NIR = 0.50 -> NDVI = (0.5-0.1)/(0.5+0.1) = 0.6667
    b11 = np.full((50, 50), 0.15, dtype="float32")

    with rasterio.open(test_file, "w", **profile) as dst:
        dst.write(b2, 1)
        dst.write(b3, 2)
        dst.write(b4, 3)
        dst.write(b8, 4)
        dst.write(b11, 5)

    processor = EOProcessor(storage_root=tmp_path)
    scene = SatelliteScene(
        scene_id="TEST_CALC_SCENE",
        file_path="test_scene.tif",
        sensor="MSI",
        bands=["B02", "B03", "B04", "B08", "B11"],
    )

    # Test NDVI
    out_rel_path, stats = processor.process_index(scene, "NDVI")
    assert stats["valid_pixels"] == 2500
    assert abs(stats["mean_value"] - 0.6667) < 0.01
    assert (tmp_path / out_rel_path).exists()

    # Test LST (Thermal)
    lst_rel_path, lst_stats = processor.process_index(scene, "LST")
    assert lst_stats["valid_pixels"] == 2500
    assert (tmp_path / lst_rel_path).exists()

    # Test Composite PNG generation
    png_path = processor.generate_composite(scene, mode="RGB")
    assert png_path.exists()
    assert png_path.suffix == ".png"

    # Test Histogram calculation
    hist = processor.compute_histogram(tmp_path / out_rel_path, "NDVI", n_bins=32)
    assert hist.total_pixels == 2500
    assert len(hist.counts) == 32
