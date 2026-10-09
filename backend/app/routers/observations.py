from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models.observation import Observation
from ..schemas.observation import ObservationOut

router = APIRouter(prefix="/observations", tags=["Observations"])


@router.get(
    "",
    response_model=list[ObservationOut],
    summary="List observations",
)
def list_observations(
    location_id: Optional[str] = Query(None, description="Filter by location ID"),
    domain_id: Optional[str] = Query(None, description="Filter by domain ID"),
    metric_name: Optional[str] = Query(None, description="Filter by metric name"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
):
    """
    Returns observations ordered by most recent first.
    Filter by `location_id`, `domain_id`, or `metric_name`.
    """
    query = db.query(Observation).order_by(Observation.observed_at.desc())

    if location_id:
        query = query.filter(Observation.location_id == location_id)
    if domain_id:
        query = query.filter(Observation.domain_id == domain_id)
    if metric_name:
        query = query.filter(Observation.metric_name == metric_name)

    observations = query.offset(offset).limit(limit).all()
    return [ObservationOut.from_orm_model(o) for o in observations]
