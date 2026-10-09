from pydantic import BaseModel
from datetime import datetime
from typing import Literal


class DomainOut(BaseModel):
    """
    API response schema for EnvironmentalDomain.
    Field names intentionally match the TypeScript EnvironmentalDomain interface
    in src/types/index.ts for seamless frontend consumption.
    """
    id: str
    name: str
    category: str
    iconName: str          # camelCase to match TS interface
    description: str
    status: Literal["Stable", "Vulnerable", "Critical Risk", "Monitoring"]
    keyIndicator: str
    indicatorValue: str
    changeRate: str
    primaryRisk: str
    affectedRegionsCount: int

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_model(cls, domain) -> "DomainOut":
        return cls(
            id=domain.id,
            name=domain.name,
            category=domain.category,
            iconName=domain.icon_name,
            description=domain.description,
            status=domain.status,
            keyIndicator=domain.key_indicator,
            indicatorValue=domain.indicator_value,
            changeRate=domain.change_rate,
            primaryRisk=domain.primary_risk,
            affectedRegionsCount=domain.affected_regions_count,
        )
