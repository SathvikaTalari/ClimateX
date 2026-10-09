from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from ..database import get_db
from ..models.location import Location
from ..schemas.location import LocationOut

router = APIRouter(prefix="/locations", tags=["Locations"])


@router.get(
    "",
    response_model=list[LocationOut],
    summary="List all observation locations",
)
def list_locations(
    domain_id: Optional[str] = Query(None, description="Filter by dominant domain ID"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    db: Session = Depends(get_db),
):
    """
    Returns all monitored observation locations.
    Optionally filter by `domain_id` or `risk_level`.
    """
    query = db.query(Location).options(joinedload(Location.key_stats))

    if domain_id:
        query = query.filter(Location.dominant_domain_id == domain_id)
    if risk_level:
        query = query.filter(Location.risk_level == risk_level)

    locations = query.order_by(Location.name).all()
    return [LocationOut.from_orm_model(loc) for loc in locations]


@router.get(
    "/{location_id}",
    response_model=LocationOut,
    summary="Get a single observation location by ID",
)
def get_location(location_id: str, db: Session = Depends(get_db)):
    """
    Returns a single observation location by ID (e.g. 'loc-1').
    """
    location = (
        db.query(Location)
        .options(joinedload(Location.key_stats))
        .filter(Location.id == location_id)
        .first()
    )
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location '{location_id}' not found.",
        )
    return LocationOut.from_orm_model(location)
