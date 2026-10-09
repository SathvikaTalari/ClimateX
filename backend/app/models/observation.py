from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from ..database import Base


class Observation(Base):
    """
    A single measured metric value for a location/domain at a point in time.
    Designed to be the primary data table for time-series environmental measurements.
    """
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(128), nullable=False, index=True)   # e.g. 'NDVI', 'LST', 'SoilMoisture'
    metric_value = Column(Float, nullable=False)
    unit = Column(String(64), nullable=True)                        # e.g. '°C', '%', 'Gt/yr'
    trend = Column(String(16), nullable=True, default="stable")     # 'up', 'down', 'stable'
    observed_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # Optional PostGIS point (for sub-location precision)
    geometry = Column(Geometry("POINT", srid=4326), nullable=True)

    # Foreign keys
    location_id = Column(
        String(32), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    domain_id = Column(
        String(64), ForeignKey("environmental_domains.id", ondelete="SET NULL"), nullable=True, index=True
    )
    scene_id = Column(
        Integer, ForeignKey("satellite_scenes.id", ondelete="SET NULL"), nullable=True, index=True
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("trend IN ('up', 'down', 'stable')", name="ck_observation_trend"),
        Index("ix_observations_location_time", "location_id", "observed_at"),
        Index("ix_observations_domain_time", "domain_id", "observed_at"),
        Index("ix_observations_geometry", "geometry", postgresql_using="gist"),
    )

    # Relationships
    location = relationship("Location", back_populates="observations")
    domain = relationship("EnvironmentalDomain", back_populates="observations")
    scene = relationship("SatelliteScene", back_populates="observations")

    def __repr__(self) -> str:
        return f"<Observation id={self.id} metric={self.metric_name!r} value={self.metric_value}>"
