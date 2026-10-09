from pydantic import BaseModel
from typing import Literal, Optional


class KeyStatOut(BaseModel):
    """
    Matches the keyStats item structure in the TypeScript ClimateLocation interface.
    """
    label: str
    value: str
    trend: Literal["up", "down", "stable"]

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_model(cls, stat) -> "KeyStatOut":
        return cls(label=stat.label, value=stat.value, trend=stat.trend)


class LocationOut(BaseModel):
    """
    API response schema for Location.
    Field names match the TypeScript ClimateLocation interface exactly.
    """
    id: str
    name: str
    region: str
    country: str
    coordinates: list[float]   # [lat, lng]
    zoom: int
    landform: str
    elevation: str
    dominantDomain: Optional[str]
    riskLevel: Literal["Low", "Moderate", "High", "Severe"]
    satelliteSensors: list[str]
    lastObservation: Optional[str]
    description: Optional[str]
    keyStats: list[KeyStatOut]

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_model(cls, loc) -> "LocationOut":
        return cls(
            id=loc.id,
            name=loc.name,
            region=loc.region,
            country=loc.country,
            coordinates=[loc.latitude, loc.longitude],
            zoom=loc.zoom,
            landform=loc.landform,
            elevation=loc.elevation,
            dominantDomain=loc.dominant_domain_id,
            riskLevel=loc.risk_level,
            satelliteSensors=loc.satellite_sensors or [],
            lastObservation=loc.last_observation,
            description=loc.description,
            keyStats=[KeyStatOut.from_orm_model(s) for s in loc.key_stats],
        )
