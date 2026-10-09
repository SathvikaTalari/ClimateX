# ClimateX — Environmental Intelligence & Earth Observation Platform

[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2014-black?logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%20%2B%20PostGIS-336791?logo=postgresql)](https://postgis.net/)
[![Python](https://img.shields.io/badge/ML--Service-Python%203.11+-3776AB?logo=python)](https://python.org/)
[![Copernicus](https://img.shields.io/badge/EO-Sentinel%20%26%20Landsat-blue)](#)

ClimateX is an environmental intelligence and Earth Observation (EO) platform designed for real-time ecological monitoring, remote-sensing analytics, and machine learning-driven change detection. It integrates high-resolution satellite imagery (Sentinel-2, Landsat-8/9) with spatial analytics to monitor critical domains such as forests, water bodies, urban heat islands, and agricultural biomes.

---

## Architecture Overview

ClimateX consists of three decoupled services and a geospatial database:

```
                          ┌─────────────────────────────┐
                          │     Next.js 14 Frontend     │
                          │        (Port 3000)          │
                          └──────────────┬──────────────┘
                                         │ REST API
                                         ▼
                          ┌─────────────────────────────┐
                          │       FastAPI Backend       │
                          │        (Port 8000)          │
                          └──┬───────────┬────────────┬─┘
                             │           │            │
            Proxy / Dispatches│           │            │ Database
                             ▼           ▼            ▼
                   ┌──────────┐     ┌─────────┐   ┌────────────────────────┐
                   │ML Service│     │EO Data  │   │ PostgreSQL 16 + PostGIS│
                   │(Port 8001│     │Storage  │   │      (Port 5432/5433)  │
                   └──────────┘     └─────────┘   └────────────────────────┘
```

1. **Frontend (`/frontend`)**: Next.js 14 (App Router) interface with interactive map exploration, climate risk assessment, predictive analytics, and environmental domain dashboards.
2. **Backend (`/backend`)**: FastAPI service handling geospatial queries, Copernicus & USGS satellite catalog integration, Earth Observation pipeline, and database migrations.
3. **ML Service (`/ml-service`)**: Microservice implementing the MISCD (Multi-Index Spectral Change Detection) algorithm using Rasterio and NumPy for vegetation, water, and built-up index change maps.
4. **Database**: PostgreSQL 16 with PostGIS extension for spatial querying, geometry/raster metadata, and time-series observations.

---

## Features

- **9 Environmental Domains**: Forest canopy health, water bodies & reservoir capacity, mountain snowpack, urban microclimates, arid boundary encroachment, and more.
- **Monitored Geographic Sites**: Key ecological hotspots across India (Telangana Forests & Amrabad Tiger Reserve, Hussain Sagar Lake basin, Western Ghats, Sundarbans, etc.).
- **Earth Observation Gateway**: Automated ingestion, index computation (NDVI, NDWI, NDBI, LST), band composites (RGB, False Color Infrared, SWIR), and cloud masking.
- **Spectral Change Detection (MISCD)**: Pre- and post-event satellite comparison with auto-generated change heatmaps and severity classification.
- **Simulation & Prediction**: Ecological risk forecasting and scenario modeling.

---

## Quick Start Guide

### Prerequisites
- [Docker & Docker Compose](https://www.docker.com/)
- [Python 3.11+](https://www.python.org/)
- [Node.js 18+](https://nodejs.org/)

---

### Step 1: Start PostgreSQL + PostGIS

From the project root:

```powershell
docker-compose up -d
```

Verify that the database container is healthy:
```powershell
docker-compose ps
```

---

### Step 2: Configure Environment Variables

Copy the example environment configurations:

```powershell
# Root / backend environment
cp .env.example backend/.env

# ML service environment
cp ml-service/.env.example ml-service/.env
```

*(Edit `backend/.env` with your Copernicus Data Space or USGS credentials if external satellite fetching is required. Demo datasets work offline without credentials).*

---

### Step 3: Run the Backend Service

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1   # On Linux/macOS: source venv/bin/activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

The database automatically seeds domains, monitored locations, and demo raster metadata on initial launch.
- Interactive API Docs: `http://localhost:8000/api/docs`

---

### Step 4: Run the ML Change Detection Service

In a separate terminal:

```powershell
cd ml-service
python -m venv venv
.\venv\Scripts\Activate.ps1   # On Linux/macOS: source venv/bin/activate
pip install -r requirements.txt

# Start ML Service
python run.py
```

- ML Service runs on: `http://localhost:8001`
- ML API Docs: `http://localhost:8001/docs`

---

### Step 5: Run the Frontend

In a separate terminal:

```powershell
cd frontend
npm install
npm run dev
```

- Web Application: `http://localhost:3000`

---

## Directory Structure

```
ClimateX_Platform/
├── backend/
│   ├── alembic/                # PostGIS database migrations
│   ├── app/
│   │   ├── eo_gateway/         # Satellite catalog connectors (Copernicus, USGS, UP42)
│   │   ├── models/             # SQLAlchemy ORM models (Locations, Domains, Scenes)
│   │   ├── routers/            # FastAPI routes
│   │   ├── services/           # EO processing, band indices, raster rendering
│   │   └── seed.py             # Idempotent database seeder
│   ├── eo_data/                # Local EO rasters, demo data, composites & change maps
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── app/                # Next.js App Router (domains, explore, risk, prediction)
│   │   ├── components/         # Reusable UI widgets, maps & analytics charts
│   │   └── lib/                # API clients and utilities
│   ├── package.json
│   └── tailwind.config.ts
├── ml-service/
│   ├── app/                    # MISCD algorithm & analysis pipeline
│   ├── run.py
│   └── requirements.txt
├── docker-compose.yml          # PostGIS container orchestration
├── .env.example
├── .gitignore
└── README.md
```

---

## License

This project is licensed under the [MIT License](LICENSE).
