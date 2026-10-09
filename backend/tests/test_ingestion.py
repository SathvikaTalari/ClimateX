import pytest
from datetime import date
from app.eo_gateway import EOScene
from app.services.ingestion import IngestionService
from app.models.satellite import SatelliteScene


def test_duplicate_detection(db_session):
    service = IngestionService()
    scene = EOScene(
        scene_id="TEST_SCENE_001",
        provider="copernicus",
        satellite="Sentinel-2A",
        sensor="MSI",
        acquisition_date=date(2026, 8, 12),
        cloud_cover=5.0,
        bbox=(77.0, 12.0, 78.0, 13.0),
    )

    # First record creation
    rec1 = service.metadata_only_record(db_session, scene)
    assert rec1.id is not None
    assert rec1.ingestion_status == "completed"

    # Check duplicate returns True
    assert service.check_duplicate(db_session, "copernicus", "TEST_SCENE_001") is True

    # Second record call returns existing row
    rec2 = service.metadata_only_record(db_session, scene)
    assert rec2.id == rec1.id
