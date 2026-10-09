from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Text, ForeignKey, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from ..database import Base


class AdministrativeArea(Base):
    """Represents a country, state, or region polygon."""
    __tablename__ = "administrative_areas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    region = Column(String(128), nullable=True)
    country = Column(String(128), nullable=False, index=True)
    level = Column(Integer, nullable=False, default=1)  # 1=country, 2=state/province, 3=district
    geometry = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    locations = relationship("Location", back_populates="administrative_area")

    def __repr__(self) -> str:
        return f"<AdministrativeArea id={self.id} name={self.name!r}>"


class Location(Base):
    """Monitored climate observation site / field station."""
    __tablename__ = "locations"

    id = Column(String(32), primary_key=True, index=True)  # e.g. 'loc-1'
    name = Column(String(255), nullable=False, index=True)
    region = Column(String(128), nullable=False)
    country = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    zoom = Column(Integer, nullable=False, default=6)
    landform = Column(String(255), nullable=False)
    elevation = Column(String(64), nullable=False)
    description = Column(Text, nullable=True)
    risk_level = Column(String(16), nullable=False, default="Moderate")
    satellite_sensors = Column(ARRAY(String), nullable=True, default=list)
    last_observation = Column(String(64), nullable=True)

    # PostGIS point geometry (EPSG:4326 WGS-84)
    geometry = Column(Geometry("POINT", srid=4326), nullable=True)

    # Foreign keys
    dominant_domain_id = Column(
        String(64), ForeignKey("environmental_domains.id", ondelete="SET NULL"), nullable=True, index=True
    )
    administrative_area_id = Column(
        Integer, ForeignKey("administrative_areas.id", ondelete="SET NULL"), nullable=True
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "risk_level IN ('Low', 'Moderate', 'High', 'Severe')",
            name="ck_location_risk_level",
        ),
        Index("ix_locations_geometry", "geometry", postgresql_using="gist"),
    )

    # Relationships
    dominant_domain = relationship("EnvironmentalDomain", back_populates="locations")
    administrative_area = relationship("AdministrativeArea", back_populates="locations")
    key_stats = relationship("LocationKeyStat", back_populates="location", cascade="all, delete-orphan")
    datasets = relationship("Dataset", back_populates="location")
    satellite_scenes = relationship("SatelliteScene", back_populates="location")
    observations = relationship("Observation", back_populates="location")

    def __repr__(self) -> str:
        return f"<Location id={self.id!r} name={self.name!r}>"


class LocationKeyStat(Base):
    """Key metric statistics displayed on a location card."""
    __tablename__ = "location_key_stats"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(
        String(32), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label = Column(String(128), nullable=False)
    value = Column(String(64), nullable=False)
    trend = Column(String(16), nullable=False, default="stable")

    __table_args__ = (
        CheckConstraint("trend IN ('up', 'down', 'stable')", name="ck_key_stat_trend"),
    )

    # Relationships
    location = relationship("Location", back_populates="key_stats")

    def __repr__(self) -> str:
        return f"<LocationKeyStat id={self.id} label={self.label!r}>"
