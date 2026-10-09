# ClimateX Backend — Phase 2

FastAPI + PostgreSQL/PostGIS backend for the ClimateX Environmental Intelligence Platform.

## Quick Start

### 1. Start PostgreSQL + PostGIS via Docker

```powershell
# From the project root (C:\ClimateX_Platform)
docker-compose up -d
```

Wait for the container to be healthy:
```powershell
docker-compose ps
```

### 2. Set Up Python Virtual Environment

```powershell
# Inside C:\ClimateX_Platform\backend\
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Run Database Migrations

```powershell
# Still inside backend\ with .venv active
alembic upgrade head
```

> The migration enables PostGIS and creates all 9 tables.

### 4. Start the FastAPI Server

```powershell
uvicorn app.main:app --reload --port 8000
```

The server auto-seeds the 9 environmental domains and 5 locations on first startup.

### 5. Verify API

```powershell
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/domains
curl http://localhost:8000/api/v1/locations
```

Or open the interactive docs: **http://localhost:8000/api/docs**

---

## Frontend Integration

With both the backend (`port 8000`) and Next.js frontend (`port 3000`) running:

- Visit `/domains` — domain cards load from the live database
- Visit `/explore` — observation sites load from the live database
- A `● Live API` badge appears in the domains page when connected

The frontend falls back to static mock data automatically if the backend is unreachable.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Service + DB health check |
| GET | `/api/v1/domains` | List all 9 environmental domains |
| GET | `/api/v1/domains/{id}` | Single domain detail |
| GET | `/api/v1/locations` | List all observation locations |
| GET | `/api/v1/locations/{id}` | Single location with key stats |
| GET | `/api/v1/observations` | List observations (filterable) |
| GET | `/api/v1/satellite-scenes` | List satellite scenes (filterable) |

### Query Parameters

**`GET /api/v1/locations`**
- `domain_id` — filter by dominant domain slug (e.g. `forest`)
- `risk_level` — filter by risk level (`Low`, `Moderate`, `High`, `Severe`)

**`GET /api/v1/observations`**
- `location_id`, `domain_id`, `metric_name`, `limit`, `offset`

**`GET /api/v1/satellite-scenes`**
- `location_id`, `domain_id`, `sensor`, `limit`, `offset`

---

## Project Structure

```
backend/
├── app/
│   ├── main.py          # FastAPI app, CORS, lifespan (auto-create tables + seed)
│   ├── config.py        # Settings via pydantic-settings
│   ├── database.py      # SQLAlchemy engine, session, Base
│   ├── seed.py          # Idempotent domain + location seeder
│   ├── models/          # SQLAlchemy ORM models
│   │   ├── user.py      # User, Role, user_roles
│   │   ├── domain.py    # EnvironmentalDomain
│   │   ├── location.py  # AdministrativeArea, Location, LocationKeyStat
│   │   ├── dataset.py   # Dataset
│   │   ├── satellite.py # SatelliteScene (PostGIS footprint + JSONB)
│   │   └── observation.py # Observation (time-series metrics)
│   ├── schemas/         # Pydantic response schemas (camelCase → TS compatible)
│   └── routers/         # FastAPI APIRouter per resource
├── alembic/             # Database migrations
│   └── versions/
│       └── 0001_initial.py
├── alembic.ini
├── requirements.txt
└── .env
```

---

## Re-seeding

The seeder is idempotent. To force a re-seed, truncate the tables:

```sql
TRUNCATE locations, environmental_domains CASCADE;
```

Then restart the server — it will re-seed automatically.

---

## Environment Variables

Copy `.env.example` at the project root to `backend/.env` and adjust as needed.

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://climatex_user:climatex_pass@localhost:5432/climatex` | SQLAlchemy connection string |
| `APP_ENV` | `development` | Application environment |
| `FRONTEND_URL` | `http://localhost:3000` | Additional CORS origin |
| `BACKEND_PORT` | `8000` | Uvicorn port |
