from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.domain import EnvironmentalDomain
from ..schemas.domain import DomainOut

router = APIRouter(prefix="/domains", tags=["Domains"])


@router.get(
    "",
    response_model=list[DomainOut],
    summary="List all environmental domains",
)
def list_domains(db: Session = Depends(get_db)):
    """
    Returns all 9 environmental domains ordered by name.
    """
    domains = db.query(EnvironmentalDomain).order_by(EnvironmentalDomain.name).all()
    return [DomainOut.from_orm_model(d) for d in domains]


@router.get(
    "/{domain_id}",
    response_model=DomainOut,
    summary="Get a single domain by ID",
)
def get_domain(domain_id: str, db: Session = Depends(get_db)):
    """
    Returns a single environmental domain by its slug ID (e.g. 'forest', 'urban-heat').
    """
    domain = db.query(EnvironmentalDomain).filter(EnvironmentalDomain.id == domain_id).first()
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain '{domain_id}' not found.",
        )
    return DomainOut.from_orm_model(domain)
