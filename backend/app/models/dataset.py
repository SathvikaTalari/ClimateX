from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Dataset(Base):
    """Represents a geospatial or tabular dataset associated with a domain or location."""
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    source = Column(String(255), nullable=True)
    data_type = Column(String(64), nullable=True)       # e.g. 'raster', 'vector', 'tabular'
    resolution = Column(String(64), nullable=True)      # e.g. '10m', '1km'
    temporal_coverage = Column(String(128), nullable=True)  # e.g. '2020-01 to 2025-12'

    # Foreign keys
    domain_id = Column(
        String(64), ForeignKey("environmental_domains.id", ondelete="SET NULL"), nullable=True, index=True
    )
    location_id = Column(
        String(32), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True, index=True
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
            "data_type IN ('raster', 'vector', 'tabular', 'point_cloud', 'time_series', 'other')",
            name="ck_dataset_data_type",
        ),
    )

    # Relationships
    domain = relationship("EnvironmentalDomain", back_populates="datasets")
    location = relationship("Location", back_populates="datasets")

    def __repr__(self) -> str:
        return f"<Dataset id={self.id} name={self.name!r}>"
