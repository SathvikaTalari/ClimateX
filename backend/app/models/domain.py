from sqlalchemy import Column, String, Integer, DateTime, Text, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class EnvironmentalDomain(Base):
    __tablename__ = "environmental_domains"

    # Slug-based primary key (e.g. 'forest', 'water-bodies')
    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    category = Column(String(128), nullable=False)
    icon_name = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(
        String(32),
        nullable=False,
        default="Monitoring",
    )
    key_indicator = Column(String(128), nullable=False)
    indicator_value = Column(String(64), nullable=False)
    change_rate = Column(String(32), nullable=False)
    primary_risk = Column(String(255), nullable=False)
    affected_regions_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('Stable', 'Vulnerable', 'Critical Risk', 'Monitoring')",
            name="ck_domain_status",
        ),
    )

    # Relationships
    locations = relationship("Location", back_populates="dominant_domain")
    datasets = relationship("Dataset", back_populates="domain")
    satellite_scenes = relationship("SatelliteScene", back_populates="domain")
    observations = relationship("Observation", back_populates="domain")

    def __repr__(self) -> str:
        return f"<EnvironmentalDomain id={self.id!r} name={self.name!r}>"
