import pytest
from datetime import date
from app.eo_gateway import SceneSearchParams, EOScene
from app.eo_gateway.copernicus import CopernicusProvider
from app.eo_gateway.usgs import USGSProvider
from app.eo_gateway.up42 import UP42Provider
from app.eo_gateway.registry import ProviderRegistry


def test_scene_search_params_bbox():
    params = SceneSearchParams(
        lat=12.9716,
        lon=77.5946,
        date_from=date(2026, 8, 1),
        date_to=date(2026, 8, 15),
    )
    bbox = params.to_bbox(radius_deg=0.1)
    assert len(bbox) == 4
    assert pytest.approx(bbox[0]) == 77.4946
    assert pytest.approx(bbox[1]) == 12.8716
    assert pytest.approx(bbox[2]) == 77.6946
    assert pytest.approx(bbox[3]) == 13.0716


def test_eoscene_provenance():
    scene = EOScene(
        scene_id="S2A_MSIL2A_TEST",
        provider="copernicus",
        satellite="Sentinel-2A",
        sensor="MSI",
        acquisition_date=date(2026, 8, 10),
        cloud_cover=12.5,
        bbox=(77.0, 12.0, 78.0, 13.0),
        resolution_m=10.0,
        source_url="https://catalogue.dataspace.copernicus.eu/stac/test",
    )
    prov = scene.provenance
    assert prov["provider"] == "copernicus"
    assert prov["scene_id"] == "S2A_MSIL2A_TEST"
    assert prov["satellite"] == "Sentinel-2A"
    assert prov["cloud_cover"] == 12.5


def test_provider_configuration_states():
    copernicus = CopernicusProvider(client_id="", client_secret="")
    # Search is public, so is_configured should be True
    assert copernicus.is_configured is True
    assert copernicus.supports_search_without_credentials is True
    assert copernicus._download_configured is False

    usgs = USGSProvider(username="", password="")
    assert usgs.is_configured is False

    up42 = UP42Provider(project_id="", project_api_key="")
    assert up42.is_configured is False


@pytest.mark.asyncio
async def test_registry_search_merge():
    copernicus = CopernicusProvider()
    registry = ProviderRegistry([copernicus])
    assert "copernicus" in registry.available_provider_names()
    assert "Sentinel-2" in registry.available_satellites()

    params = SceneSearchParams(
        lat=12.9716,
        lon=77.5946,
        date_from=date(2026, 8, 1),
        date_to=date(2026, 8, 15),
        limit=5,
    )
    # Search with Copernicus provider (should succeed or return empty list without crashing)
    results = await registry.search_all_providers(params)
    assert isinstance(results, list)
