from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from ..database import Base

class ProcessedImage(Base):
    """Stores metadata for processed Earth Observation imagery (e.g. COGs)."""
    __tablename__ = "processed_images"

    id = Column(Integer, primary_key=True, index=True)
    scene_id = Column(Integer, ForeignKey("satellite_scenes.id", ondelete="CASCADE"), nullable=False, index=True)
    index_name = Column(String(32), nullable=False, index=True) # e.g. "NDVI", "NDWI", "NDBI"
    
    file_path = Column(String(512), nullable=False) # path to COG relative to storage
    resolution_m = Column(Float, nullable=True)
    crs = Column(String(64), nullable=True)
    bounds = Column(JSONB, nullable=True) # [minx, miny, maxx, maxy]
    
    status = Column(String(32), nullable=False, default="processing", index=True) # "processing", "completed", "failed"
    error_message = Column(String(1024), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    scene = relationship("SatelliteScene")

class SpatialFeature(Base):
    """Stores zonal statistics extracted from processed imagery for a specific location."""
    __tablename__ = "spatial_features"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(String(32), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    processed_image_id = Column(Integer, ForeignKey("processed_images.id", ondelete="CASCADE"), nullable=True, index=True)
    
    index_name = Column(String(32), nullable=False, index=True) # e.g. "NDVI", "NDWI", "NDBI"
    
    # Zonal statistics
    mean_value = Column(Float, nullable=True)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    std_dev = Column(Float, nullable=True)
    valid_pixels = Column(Integer, nullable=True)
    
    # Boundary used for extraction
    geometry = Column(Geometry("POLYGON", srid=4326), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    location = relationship("Location")
    processed_image = relationship("ProcessedImage")
