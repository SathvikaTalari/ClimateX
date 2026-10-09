"""
Seed script for ClimateX database.
Seeds the 9 environmental domains and 9 monitored Indian locations.
This script is idempotent — it updates existing records or inserts new ones.
"""
from sqlalchemy.orm import Session
from .models.domain import EnvironmentalDomain
from .models.location import Location, LocationKeyStat


# ─── Environmental Domains ────────────────────────────────────────────────────
DOMAINS = [
    {
        "id": "forest",
        "name": "Forest",
        "category": "Terrestrial Ecosystem",
        "icon_name": "Trees",
        "description": "Telangana forests, Western Ghats canopy coverage, canopy health, deforestation frontiers, and carbon sink dynamics.",
        "status": "Vulnerable",
        "key_indicator": "Tree Canopy Loss",
        "indicator_value": "2.4M Ha / yr",
        "change_rate": "-1.8%",
        "primary_risk": "Wildfire & Illegal Logging",
        "affected_regions_count": 142,
    },
    {
        "id": "water-bodies",
        "name": "Water Bodies",
        "category": "Hydrological Systems",
        "icon_name": "Waves",
        "description": "Hussain Sagar, Indian lakes & reservoirs, freshwater capacity, river basin discharge, and wetland degradation.",
        "status": "Critical Risk",
        "key_indicator": "Freshwater Volume Index",
        "indicator_value": "68.4%",
        "change_rate": "-3.2%",
        "primary_risk": "Severe Drought & Pollution",
        "affected_regions_count": 189,
    },
    {
        "id": "mountains",
        "name": "Mountains",
        "category": "High Altitude Biomes",
        "icon_name": "Mountain",
        "description": "Himalayas, Western Ghats, glacial retreat, slope stability, alpine corridors, and snowpack cover.",
        "status": "Vulnerable",
        "key_indicator": "Glacial Mass Balance",
        "indicator_value": "-420 Gt / yr",
        "change_rate": "-4.1%",
        "primary_risk": "Glacial Lake Outbursts",
        "affected_regions_count": 78,
    },
    {
        "id": "plains",
        "name": "Plains",
        "category": "Lowland Grasslands",
        "icon_name": "Compass",
        "description": "Telangana plains, Indo-Gangetic alluvial plains, soil organic carbon, wind erosion, and agricultural land cover.",
        "status": "Stable",
        "key_indicator": "Soil Organic Carbon",
        "indicator_value": "48.2 t/Ha",
        "change_rate": "+0.4%",
        "primary_risk": "Desertification & Dust Storms",
        "affected_regions_count": 95,
    },
    {
        "id": "coastal-areas",
        "name": "Coastal Areas",
        "category": "Marine-Land Interface",
        "icon_name": "Anchor",
        "description": "Visakhapatnam, Andhra & Indian coastline, mangrove buffer preservation, cyclone storm surge, and coastal erosion.",
        "status": "Critical Risk",
        "key_indicator": "Mean Sea Level Anomaly",
        "indicator_value": "+4.8 mm / yr",
        "change_rate": "+2.1%",
        "primary_risk": "Coastal Inundation",
        "affected_regions_count": 230,
    },
    {
        "id": "urban-areas",
        "name": "Urban Areas",
        "category": "Built Environment",
        "icon_name": "Building2",
        "description": "Hyderabad, Bengaluru, Mumbai megacities, built infrastructure expansion, flash flood resilience, and urban canopy.",
        "status": "Vulnerable",
        "key_indicator": "Impervious Surface Ratio",
        "indicator_value": "64.1%",
        "change_rate": "+2.8%",
        "primary_risk": "Flash Flooding & Infrastructure Strain",
        "affected_regions_count": 310,
    },
    {
        "id": "urban-heat",
        "name": "Urban Heat",
        "category": "Microclimate Anomalies",
        "icon_name": "ThermometerSun",
        "description": "Hyderabad, Delhi, Ahmedabad urban heat islands, thermal hot spots, land surface temperature anomalies, and cooling corridors.",
        "status": "Critical Risk",
        "key_indicator": "Surface Heat Delta",
        "indicator_value": "+5.4 °C",
        "change_rate": "+1.6%",
        "primary_risk": "Extreme Heat Waves & Health Stress",
        "affected_regions_count": 275,
    },
    {
        "id": "agriculture",
        "name": "Agriculture",
        "category": "Food Production Systems",
        "icon_name": "Wheat",
        "description": "Telangana, Andhra Pradesh, Punjab fertile agricultural belts, crop health (NDVI), irrigation efficiency, and soil health.",
        "status": "Vulnerable",
        "key_indicator": "Agri Vegetation Index",
        "indicator_value": "0.62 NDVI",
        "change_rate": "-1.1%",
        "primary_risk": "Crop Stress & Hydrological Deficit",
        "affected_regions_count": 198,
    },
    {
        "id": "deserts",
        "name": "Deserts",
        "category": "Arid & Semi-Arid Ecosystems",
        "icon_name": "Sun",
        "description": "Rajasthan, Thar Desert arid margins, sand dune mobility, hyper-arid microclimate monitoring, and boundary expansion.",
        "status": "Monitoring",
        "key_indicator": "Aridity Index Trend",
        "indicator_value": "0.14 AI",
        "change_rate": "+1.9%",
        "primary_risk": "Arid Boundary Encroachment",
        "affected_regions_count": 64,
    },
]


# ─── Locations ────────────────────────────────────────────────────────────────
LOCATIONS = [
    {
        "id": "loc-1",
        "name": "Telangana Forests & Nallamala Belt",
        "region": "South India",
        "country": "India",
        "latitude": 16.3544,
        "longitude": 78.8472,
        "zoom": 8,
        "landform": "Tropical Deciduous Forest & Hill Ranges",
        "elevation": "420m ASL",
        "dominant_domain_id": "forest",
        "risk_level": "Severe",
        "satellite_sensors": ["Sentinel-2 MSI", "Landsat-9 OLI", "Sentinel-1 SAR"],
        "last_observation": "2026-08-16 10:30 IST",
        "description": "Amrabad & Nallamala deciduous forest ecosystem in Telangana monitoring canopy health, deforestation pressure, and seasonal forest fire risk.",
        "key_stats": [
            {"label": "Canopy Density", "value": "78.4%", "trend": "stable"},
            {"label": "NDVI Score", "value": "0.74", "trend": "down"},
            {"label": "Surface Temp", "value": "31.2°C", "trend": "up"},
        ],
    },
    {
        "id": "loc-2",
        "name": "Hussain Sagar & Hyderabad Basins",
        "region": "South India",
        "country": "India",
        "latitude": 17.4239,
        "longitude": 78.4738,
        "zoom": 11,
        "landform": "Urban Lake Basin & Hydrological Catchment",
        "elevation": "533m ASL",
        "dominant_domain_id": "water-bodies",
        "risk_level": "Severe",
        "satellite_sensors": ["Sentinel-2 MSI", "Landsat-9", "Sentinel-3 OLCI"],
        "last_observation": "2026-08-16 11:15 IST",
        "description": "Major urban reservoir in Hyderabad, Telangana monitored for catchment runoff, turbidity index, and wetland preservation.",
        "key_stats": [
            {"label": "Freshwater Area", "value": "4.4 km²", "trend": "stable"},
            {"label": "Turbidity Index", "value": "Moderate", "trend": "down"},
            {"label": "Inflow Vol Delta", "value": "+12.4%", "trend": "up"},
        ],
    },
    {
        "id": "loc-3",
        "name": "Himalayan Glacial & Alpine Belt",
        "region": "North India",
        "country": "India",
        "latitude": 32.2190,
        "longitude": 77.1887,
        "zoom": 8,
        "landform": "High Mountain Alpine Glacial System",
        "elevation": "4,800m ASL",
        "dominant_domain_id": "mountains",
        "risk_level": "Severe",
        "satellite_sensors": ["MODIS Terra", "Sentinel-1 SAR", "ICESat-2"],
        "last_observation": "2026-08-16 08:45 IST",
        "description": "Critical Himalayan water tower supplying major Indian river basins experiencing glacial retreat and outburst lake vulnerabilities.",
        "key_stats": [
            {"label": "Glacial Ablation Rate", "value": "-1.2% / yr", "trend": "down"},
            {"label": "Outburst Risk", "value": "High", "trend": "up"},
            {"label": "Snow Cover", "value": "64.8%", "trend": "down"},
        ],
    },
    {
        "id": "loc-4",
        "name": "Deccan Plateau Plains",
        "region": "South India",
        "country": "India",
        "latitude": 17.9689,
        "longitude": 79.5941,
        "zoom": 9,
        "landform": "Semi-Arid Lowland Plateau Plains",
        "elevation": "302m ASL",
        "dominant_domain_id": "plains",
        "risk_level": "Moderate",
        "satellite_sensors": ["Sentinel-2", "SMAP Soil Moisture", "Landsat-9"],
        "last_observation": "2026-08-16 09:50 IST",
        "description": "Semi-arid agricultural plains across Telangana monitored for soil organic carbon, moisture retention, and seasonal drought resilience.",
        "key_stats": [
            {"label": "Soil Organic Carbon", "value": "42.1 t/Ha", "trend": "stable"},
            {"label": "Soil Moisture", "value": "18.4%", "trend": "down"},
            {"label": "Vegetation Cover", "value": "46.2%", "trend": "up"},
        ],
    },
    {
        "id": "loc-5",
        "name": "Visakhapatnam Coast & Bay of Bengal",
        "region": "South-East Coast",
        "country": "India",
        "latitude": 17.6868,
        "longitude": 83.2185,
        "zoom": 10,
        "landform": "Coastal Marine Shelf & Estuarine Interface",
        "elevation": "5m ASL",
        "dominant_domain_id": "coastal-areas",
        "risk_level": "High",
        "satellite_sensors": ["Sentinel-2", "VIIRS Thermal", "Sentinel-1 SAR"],
        "last_observation": "2026-08-16 12:00 IST",
        "description": "Andhra Pradesh coastal zone facing Bay of Bengal tropical storm surges, shoreline erosion, and coastal infrastructure exposure.",
        "key_stats": [
            {"label": "Sea Level Surge Def", "value": "2.8m", "trend": "up"},
            {"label": "Erosion Rate", "value": "0.4m / yr", "trend": "up"},
            {"label": "SST Anomaly", "value": "+1.4°C", "trend": "up"},
        ],
    },
    {
        "id": "loc-6",
        "name": "Greater Hyderabad Megacity",
        "region": "South India",
        "country": "India",
        "latitude": 17.3850,
        "longitude": 78.4867,
        "zoom": 10,
        "landform": "Built Metropolis & Urban Basin",
        "elevation": "542m ASL",
        "dominant_domain_id": "urban-areas",
        "risk_level": "High",
        "satellite_sensors": ["Sentinel-2", "Landsat-9", "ECOSTRESS"],
        "last_observation": "2026-08-16 13:10 IST",
        "description": "Rapidly expanding metropolitan hub in Telangana monitored for impervious surface ratio, urban expansion, and flash flood drainage.",
        "key_stats": [
            {"label": "Impervious Surface", "value": "68.2%", "trend": "up"},
            {"label": "Green Cover Ratio", "value": "14.8%", "trend": "down"},
            {"label": "Drainage Capacity", "value": "Moderate", "trend": "stable"},
        ],
    },
    {
        "id": "loc-7",
        "name": "Hyderabad Core & HITEC City Heat Island",
        "region": "South India",
        "country": "India",
        "latitude": 17.4435,
        "longitude": 78.3772,
        "zoom": 12,
        "landform": "Urban Thermal Hotspot & Commercial District",
        "elevation": "580m ASL",
        "dominant_domain_id": "urban-heat",
        "risk_level": "Severe",
        "satellite_sensors": ["Sentinel-2", "Landsat-9 Thermal", "ECOSTRESS"],
        "last_observation": "2026-08-16 14:00 IST",
        "description": "High-density tech corridor in Hyderabad experiencing severe land surface temperature (LST) anomalies and heatwave intensity.",
        "key_stats": [
            {"label": "Surface Heat Delta", "value": "+5.8°C", "trend": "up"},
            {"label": "Max LST Temp", "value": "44.2°C", "trend": "up"},
            {"label": "Cool Roof Adoption", "value": "22.4%", "trend": "up"},
        ],
    },
    {
        "id": "loc-8",
        "name": "Godavari Basin Agricultural Belt",
        "region": "South-East India",
        "country": "India",
        "latitude": 16.9891,
        "longitude": 81.7835,
        "zoom": 9,
        "landform": "Arable River Basin & Alluvial Plain",
        "elevation": "25m ASL",
        "dominant_domain_id": "agriculture",
        "risk_level": "Moderate",
        "satellite_sensors": ["Sentinel-2 MSI", "Landsat-9 OLI", "MODIS"],
        "last_observation": "2026-08-16 10:00 IST",
        "description": "Fertile agricultural region across Telangana & Andhra Pradesh monitored for paddy vegetation indices (NDVI) and canal water distribution.",
        "key_stats": [
            {"label": "Agri NDVI Index", "value": "0.68", "trend": "up"},
            {"label": "Irrigation Deficit", "value": "-6.2%", "trend": "down"},
            {"label": "Crop Health Score", "value": "82 / 100", "trend": "up"},
        ],
    },
    {
        "id": "loc-9",
        "name": "Thar Desert & Jaisalmer Margin",
        "region": "North-West India",
        "country": "India",
        "latitude": 26.9157,
        "longitude": 70.9083,
        "zoom": 8,
        "landform": "Arid Sand Dunes & Hyper-Arid Steppe",
        "elevation": "225m ASL",
        "dominant_domain_id": "deserts",
        "risk_level": "Severe",
        "satellite_sensors": ["Sentinel-3 OLCI", "SMAP Soil Moisture", "Landsat-9"],
        "last_observation": "2026-08-16 09:30 IST",
        "description": "Arid desert frontier in Rajasthan facing active dune movement, extreme surface heat index, and desert boundary encroachment.",
        "key_stats": [
            {"label": "Aridity Index", "value": "0.12 AI", "trend": "down"},
            {"label": "Soil Moisture", "value": "4.2%", "trend": "down"},
            {"label": "Dune Shift Velocity", "value": "1.8m / yr", "trend": "up"},
        ],
    },
]


def seed_database(db: Session) -> None:
    """Idempotent seed — updates existing or inserts new domains & locations."""
    _seed_domains(db)
    _seed_locations(db)
    _seed_sample_satellite_scenes(db)


def _seed_domains(db: Session) -> None:
    existing = {d.id: d for d in db.query(EnvironmentalDomain).all()}

    for data in DOMAINS:
        dom_id = data["id"]
        if dom_id in existing:
            # Update existing domain with Indian environment details
            dom = existing[dom_id]
            for key, value in data.items():
                setattr(dom, key, value)
        else:
            db.add(EnvironmentalDomain(**data))

    db.commit()
    print(f"[seed] Seeded {len(DOMAINS)} Indian environmental domain(s).")


def _seed_locations(db: Session) -> None:
    existing = {loc.id: loc for loc in db.query(Location).all()}

    for data in LOCATIONS:
        data_copy = dict(data)
        loc_id = data_copy["id"]
        key_stats_data = data_copy.pop("key_stats", [])

        if loc_id in existing:
            loc = existing[loc_id]
            for key, value in data_copy.items():
                setattr(loc, key, value)
            # Update key stats
            db.query(LocationKeyStat).filter(LocationKeyStat.location_id == loc_id).delete()
            loc.key_stats = [LocationKeyStat(location_id=loc_id, **s) for s in key_stats_data]
        else:
            loc = Location(**data_copy)
            loc.key_stats = [LocationKeyStat(location_id=loc_id, **s) for s in key_stats_data]
            db.add(loc)

    db.commit()
    print(f"[seed] Seeded {len(LOCATIONS)} Indian location(s).")


def _seed_sample_satellite_scenes(db: Session) -> None:
    from pathlib import Path
    from datetime import date, datetime, timezone
    import numpy as np
    import rasterio
    from rasterio.transform import from_origin
    from app.config import get_settings
    from app.models.satellite import SatelliteScene

    settings = get_settings()
    storage_root = Path(settings.eo_storage_path)

    for loc in LOCATIONS:
        loc_id = loc["id"]
        lat = loc["latitude"]
        lon = loc["longitude"]
        domain_id = loc["dominant_domain_id"]

        scene_id = f"S2A_MSIL2A_{loc_id.upper().replace('-', '_')}_RASTER_DEMO"
        rel_path = f"copernicus/{scene_id}/scene.tif"
        full_path = storage_root / rel_path

        # Generate realistic 256x256 multi-spectral raster with geographic features
        full_path.parent.mkdir(parents=True, exist_ok=True)
        transform = from_origin(lon - 0.05, lat + 0.05, 0.0004, 0.0004)
        profile = {
            "driver": "GTiff",
            "height": 256,
            "width": 256,
            "count": 5,
            "dtype": "float32",
            "crs": "EPSG:4326",
            "transform": transform,
            "tiled": True,
            "blockxsize": 256,
            "blockysize": 256,
            "compress": "lzw",
        }
        np.random.seed(abs(hash(loc_id)) % 2**31)

        H, W = 256, 256
        y, x = np.ogrid[:H, :W]

        # 1. Topography terrain hillshading
        hillshading = 0.03 * np.sin(x / 18.0) * np.cos(y / 18.0) + 0.02 * np.sin((x + y) / 10.0)

        # 2. Water Feature (Lake or Winding River)
        if domain_id == "water-bodies":
            r_dist = np.sqrt((x - 128) ** 2 + (y - 128) ** 2)
            water_mask = np.clip(1.0 - (r_dist / 90.0), 0.0, 1.0)
            island_mask = np.clip(1.0 - (r_dist / 25.0), 0.0, 1.0)
            water_mask = np.clip(water_mask - island_mask, 0.0, 1.0)
        else:
            river_center = 128 + 50 * np.sin(x / 35.0) + 15 * np.cos(x / 16.0)
            water_mask = np.clip(np.exp(-((y - river_center) ** 2) / 120.0), 0.0, 1.0)

        # 3. Urban & Vegetation Features
        if domain_id in ("urban-areas", "urban-heat"):
            urban_blocks = ((np.sin(x / 12.0) > -0.3) & (np.sin(y / 12.0) > -0.3)).astype(float)
            urban_mask = np.clip(urban_blocks * (1.0 - water_mask), 0.0, 1.0)
            veg_mask = np.clip((1.0 - urban_mask) * (1.0 - water_mask) * 0.4, 0.0, 1.0)
        elif domain_id == "deserts":
            urban_mask = np.zeros((H, W), dtype=float)
            veg_mask = np.zeros((H, W), dtype=float)
        else:
            urban_blocks = ((np.sin(x / 8.0) > 0.6) & (np.sin(y / 8.0) > 0.6)).astype(float)
            urban_mask = np.clip(urban_blocks * (1.0 - water_mask) * 0.25, 0.0, 1.0)
            veg_mask = np.clip((1.0 - water_mask) * (1.0 - urban_mask), 0.0, 1.0)

        # Sentinel-2 Surface Reflectance (BOA) Physics:
        # B02 (Blue), B03 (Green), B04 (Red), B08 (NIR), B11 (SWIR)
        if domain_id == "deserts":
            arr_b2 = np.clip(0.18 + hillshading, 0.01, 1.0).astype("float32")
            arr_b3 = np.clip(0.28 + hillshading, 0.01, 1.0).astype("float32")
            arr_b4 = np.clip(0.38 + hillshading, 0.01, 1.0).astype("float32")
            arr_b8 = np.clip(0.42 + hillshading, 0.01, 1.0).astype("float32")
            arr_b11 = np.clip(0.52 + hillshading, 0.01, 1.0).astype("float32")
        else:
            arr_b2 = np.clip(0.04 * veg_mask + 0.14 * water_mask + 0.16 * urban_mask + 0.08 * (1 - veg_mask - water_mask - urban_mask) + hillshading, 0.01, 1.0).astype("float32")
            arr_b3 = np.clip(0.09 * veg_mask + 0.12 * water_mask + 0.18 * urban_mask + 0.10 * (1 - veg_mask - water_mask - urban_mask) + hillshading, 0.01, 1.0).astype("float32")
            arr_b4 = np.clip(0.03 * veg_mask + 0.03 * water_mask + 0.20 * urban_mask + 0.12 * (1 - veg_mask - water_mask - urban_mask) + hillshading, 0.01, 1.0).astype("float32")
            arr_b8 = np.clip(0.52 * veg_mask + 0.01 * water_mask + 0.24 * urban_mask + 0.18 * (1 - veg_mask - water_mask - urban_mask) + hillshading, 0.01, 1.0).astype("float32")
            arr_b11 = np.clip(0.12 * veg_mask + 0.005 * water_mask + 0.42 * urban_mask + 0.22 * (1 - veg_mask - water_mask - urban_mask) + hillshading, 0.01, 1.0).astype("float32")

        with rasterio.open(full_path, "w", **profile) as dst:
            dst.write(arr_b2, 1)
            dst.write(arr_b3, 2)
            dst.write(arr_b4, 3)
            dst.write(arr_b8, 4)
            dst.write(arr_b11, 5)

        existing = db.query(SatelliteScene).filter(SatelliteScene.scene_id == scene_id).first()
        if not existing:
            scene = SatelliteScene(
                scene_id=scene_id,
                provider="copernicus",
                satellite="Sentinel-2A",
                sensor="MSI",
                acquisition_date=date(2026, 8, 15),
                cloud_cover=1.5,
                resolution_m=10.0,
                bbox_min_lon=lon - 0.05,
                bbox_min_lat=lat - 0.05,
                bbox_max_lon=lon + 0.05,
                bbox_max_lat=lat + 0.05,
                file_path=rel_path,
                file_size_bytes=full_path.stat().st_size if full_path.exists() else 200000,
                crs="EPSG:4326",
                bands=["B02", "B03", "B04", "B08", "B11"],
                ingestion_status="completed",
                ingested_at=datetime.now(timezone.utc),
                location_id=loc_id,
                domain_id=domain_id,
            )
            db.add(scene)
            db.commit()
            db.refresh(scene)
        else:
            scene = existing

        # Pre-compute all 4 environmental indices for instant display
        from app.services.eo_processor import get_eo_processor
        from app.models.location import Location
        from app.models.processing import ProcessedImage, SpatialFeature

        processor = get_eo_processor()
        location_obj = db.query(Location).filter(Location.id == loc_id).first()

        for idx_name in ("NDVI", "NDWI", "NDBI", "LST"):
            try:
                rel_out_path, stats = processor.process_index(scene, idx_name, location_obj)

                proc_rec = db.query(ProcessedImage).filter(
                    ProcessedImage.scene_id == scene.id,
                    ProcessedImage.index_name == idx_name
                ).first()
                if not proc_rec:
                    proc_rec = ProcessedImage(
                        scene_id=scene.id,
                        index_name=idx_name,
                        file_path=str(rel_out_path),
                        status="completed",
                        completed_at=datetime.now(timezone.utc),
                        resolution_m=scene.resolution_m,
                        crs=scene.crs,
                    )
                    db.add(proc_rec)
                    db.commit()
                    db.refresh(proc_rec)
                else:
                    proc_rec.file_path = str(rel_out_path)
                    proc_rec.status = "completed"
                    db.commit()

                feat = db.query(SpatialFeature).filter(
                    SpatialFeature.location_id == loc_id,
                    SpatialFeature.index_name == idx_name
                ).first()
                if not feat:
                    feat = SpatialFeature(
                        location_id=loc_id,
                        processed_image_id=proc_rec.id,
                        index_name=idx_name,
                        mean_value=stats["mean_value"],
                        min_value=stats["min_value"],
                        max_value=stats["max_value"],
                        std_dev=stats.get("std_dev"),
                        valid_pixels=stats["valid_pixels"],
                    )
                    db.add(feat)
                    db.commit()
                else:
                    feat.processed_image_id = proc_rec.id
                    feat.mean_value = stats["mean_value"]
                    feat.min_value = stats["min_value"]
                    feat.max_value = stats["max_value"]
                    feat.std_dev = stats.get("std_dev")
                    feat.valid_pixels = stats["valid_pixels"]
                    db.commit()
            except Exception as e:
                db.rollback()
                print(f"[seed] Warning: could not pre-compute {idx_name} for {loc_id}: {e}")

    print(f"[seed] Seeded and pre-computed demo satellite EO features for all {len(LOCATIONS)} locations.")
