from datetime import date


def test_list_satellite_scenes_empty(client):
    res = client.get("/api/v1/satellite-scenes")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_post_search_scenes(client):
    payload = {
        "date_from": "2026-08-01",
        "date_to": "2026-08-15",
        "lat": 12.9716,
        "lon": 77.5946,
        "satellite": "Sentinel-2",
        "cloud_cover_max": 20.0,
        "limit": 5,
    }
    res = client.post("/api/v1/satellite-scenes/search", json=payload)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_ingest_and_get_scene_lifecycle(client):
    # Step 1: Ingest metadata scene
    payload = {
        "scene_id": "S2B_TEST_SCENE_999",
        "provider": "copernicus",
        "satellite": "Sentinel-2B",
        "sensor": "MSI",
        "acquisition_date": "2026-08-14",
        "cloud_cover": 8.5,
        "resolution_m": 10.0,
        "bbox": [77.5, 12.8, 77.7, 13.1],
        "download_raster": False,  # metadata-only for test
    }
    res = client.post("/api/v1/satellite-scenes/ingest", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["scene_id"] == "S2B_TEST_SCENE_999"
    assert data["ingestion_status"] == "completed"

    scene_db_id = data["id"]

    # Step 2: Get scene metadata
    res_get = client.get(f"/api/v1/satellite-scenes/{scene_db_id}")
    assert res_get.status_code == 200
    assert res_get.json()["scene_id"] == "S2B_TEST_SCENE_999"

    # Step 3: Get status
    res_status = client.get(f"/api/v1/satellite-scenes/ingestion/{scene_db_id}/status")
    assert res_status.status_code == 200
    assert res_status.json()["ingestion_status"] == "completed"

    # Step 4: Get footprint
    res_footprint = client.get(f"/api/v1/satellite-scenes/{scene_db_id}/footprint")
    assert res_footprint.status_code == 200
    assert res_footprint.json()["footprint_geojson"] is not None

    # Step 5: By location query
    res_loc = client.get("/api/v1/satellite-scenes/by-location?lat=12.9&lon=77.6")
    assert res_loc.status_code == 200
    scenes = res_loc.json()
    assert any(s["scene_id"] == "S2B_TEST_SCENE_999" for s in scenes)
