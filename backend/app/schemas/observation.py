from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal


class ObservationOut(BaseModel):
    id: int
    metric_name: str
    metric_value: float
    unit: Optional[str]
    trend: Optional[Literal["up", "down", "stable"]]
    observed_at: datetime
    location_id: str
    domain_id: Optional[str]
    scene_id: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_model(cls, obs) -> "ObservationOut":
        return cls(
            id=obs.id,
            metric_name=obs.metric_name,
            metric_value=obs.metric_value,
            unit=obs.unit,
            trend=obs.trend,
            observed_at=obs.observed_at,
            location_id=obs.location_id,
            domain_id=obs.domain_id,
            scene_id=obs.scene_id,
            created_at=obs.created_at,
        )
