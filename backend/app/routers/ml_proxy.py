"""
ML Proxy Router — Phase 5B.

Forwards frontend requests to the ML service via httpx.
This keeps ML service internals (port 8001) hidden from the browser.

The frontend only ever talks to the main backend (port 8000).
The backend forwards to port 8001 and returns the response verbatim.

Endpoint mapping:
  Frontend → Backend                               → ML Service
  POST /api/v1/ml/change-detection                 → POST /api/v1/ml/change-detection
  GET  /api/v1/ml/jobs/{job_id}                    → GET  /api/v1/ml/jobs/{job_id}
  GET  /api/v1/ml/jobs/{job_id}/result             → GET  /api/v1/ml/jobs/{job_id}/result
  GET  /api/v1/ml/results/{result_id}              → GET  /api/v1/ml/results/{result_id}
  GET  /api/v1/ml/change-maps/{job_id}/file        → GET  /api/v1/ml/change-maps/{job_id}/file
  GET  /api/v1/ml/scenes/{location_id}/ingested    → [local DB query, no ML service call]
"""
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db

log = logging.getLogger(__name__)
router = APIRouter(prefix="/ml", tags=["ML Change Detection"])
settings = get_settings()

# httpx client reuse — created once per process
_http_client: Optional[httpx.AsyncClient] = None


def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            base_url=settings.ml_service_url,
            timeout=httpx.Timeout(120.0, connect=10.0),
        )
    return _http_client


async def _proxy(
    method: str,
    path: str,
    body: Optional[bytes] = None,
    content_type: str = "application/json",
) -> Response:
    """Forward a request to the ML service and return the response."""
    client = get_http_client()
    headers = {"Content-Type": content_type} if body else {}
    try:
        resp = await client.request(method, path, content=body, headers=headers)
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=(
                "ML service is not reachable. "
                "Start it with: cd ml-service && python run.py"
            ),
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="ML service did not respond in time.",
        )

    if resp.status_code >= 500:
        log.error("ML service error %d: %s", resp.status_code, resp.text[:500])
        raise HTTPException(
            status_code=502,
            detail=f"ML service returned an error: {resp.text[:300]}",
        )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type", "application/json"),
    )


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post(
    "/change-detection",
    status_code=202,
    summary="Submit a satellite change-detection analysis job",
)
async def submit_change_detection(request: Request):
    """Proxy: POST to ML service /api/v1/ml/change-detection."""
    body = await request.body()
    return await _proxy("POST", "/api/v1/ml/change-detection", body)


@router.get(
    "/jobs/{job_id}",
    summary="Poll job status (includes result when completed)",
)
async def get_job(job_id: str):
    return await _proxy("GET", f"/api/v1/ml/jobs/{job_id}")


@router.get(
    "/jobs/{job_id}/result",
    summary="Get result for a completed job",
)
async def get_job_result(job_id: str):
    return await _proxy("GET", f"/api/v1/ml/jobs/{job_id}/result")


@router.get(
    "/results/{result_id}",
    summary="Get a result by result ID",
)
async def get_result(result_id: str):
    return await _proxy("GET", f"/api/v1/ml/results/{result_id}")


@router.get(
    "/change-maps/{job_id}/file",
    summary="Download change-map GeoTIFF",
)
async def get_change_map_file(job_id: str):
    """Stream the change-map GeoTIFF from the ML service."""
    client = get_http_client()
    try:
        async with client.stream("GET", f"/api/v1/ml/change-maps/{job_id}/file") as ml_resp:
            if ml_resp.status_code == 404:
                raise HTTPException(status_code=404, detail="Change map not found.")
            if ml_resp.status_code >= 400:
                raise HTTPException(status_code=ml_resp.status_code, detail="ML service error.")
            content = await ml_resp.aread()
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="ML service not reachable.")

    return Response(
        content=content,
        media_type="image/tiff",
        headers={"Content-Disposition": f"attachment; filename=change_map_{job_id}.tif"},
    )


@router.get(
    "/change-maps/{job_id}/preview",
    summary="Get change-map colored PNG preview",
)
async def get_change_map_preview(job_id: str):
    """Stream the colored PNG preview of the change map."""
    client = get_http_client()
    try:
        async with client.stream("GET", f"/api/v1/ml/change-maps/{job_id}/preview") as ml_resp:
            if ml_resp.status_code == 404:
                raise HTTPException(status_code=404, detail="Change map preview not found.")
            if ml_resp.status_code >= 400:
                raise HTTPException(status_code=ml_resp.status_code, detail="ML service error.")
            content = await ml_resp.aread()
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="ML service not reachable.")

    return Response(
        content=content,
        media_type="image/png",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )

@router.post(
    "/demo/{location_id}",
    status_code=202,
    summary="Run a demo change-detection analysis with synthetic data (no real scenes needed)",
)
async def run_demo_analysis(location_id: str):
    """Proxy: POST to ML service /api/v1/ml/demo/{location_id}."""
    return await _proxy("POST", f"/api/v1/ml/demo/{location_id}")


# ─── Local helper endpoint (no ML call needed) ────────────────────────────────

@router.get(
    "/scenes/{location_id}/ingested",
    summary="List ingested (raster-ready) scenes for a location, for scene selection",
)
def list_ingested_scenes(
    location_id: str,
    db: Session = Depends(get_db),
):
    """
    Returns scenes with completed ingestion + at least one completed Phase 5A
    processed image (NDVI/NDWI/NDBI).  These are the only scenes that can be
    used in change detection.

    Answered locally — no ML service call.
    """
    from sqlalchemy import text

    rows = db.execute(
        text(
            """
            SELECT DISTINCT
                ss.id,
                ss.scene_id,
                ss.satellite,
                ss.sensor,
                ss.acquisition_date,
                ss.cloud_cover,
                ss.resolution_m,
                array_agg(DISTINCT pi.index_name ORDER BY pi.index_name) AS indices
            FROM satellite_scenes ss
            JOIN processed_images pi
              ON pi.scene_id = ss.id
             AND pi.status = 'completed'
             AND pi.file_path IS NOT NULL
             AND pi.file_path <> ''
            WHERE ss.location_id = :loc_id
              AND ss.ingestion_status = 'completed'
            GROUP BY
                ss.id, ss.scene_id, ss.satellite, ss.sensor,
                ss.acquisition_date, ss.cloud_cover, ss.resolution_m
            ORDER BY ss.acquisition_date ASC
            """
        ),
        {"loc_id": location_id},
    ).fetchall()

    return [
        {
            "db_id": row[0],
            "scene_id": row[1],
            "satellite": row[2],
            "sensor": row[3],
            "acquisition_date": str(row[4]),
            "cloud_cover": row[5],
            "resolution_m": row[6],
            "available_indices": row[7] if row[7] else [],
        }
        for row in rows
    ]
