from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, List
from datetime import datetime


class ProcessingRequest(BaseModel):
    index_name: str  # "NDVI" | "NDWI" | "NDBI" | "LST"
    location_id: Optional[str] = None


class ProcessedImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scene_id: int
    index_name: str
    file_path: str
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    @classmethod
    def from_orm_model(cls, obj: Any) -> "ProcessedImageOut":
        return cls.model_validate(obj)


class SpatialFeatureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    location_id: str
    processed_image_id: Optional[int] = None
    index_name: str
    mean_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    std_dev: Optional[float] = None
    valid_pixels: Optional[int] = None
    created_at: datetime

    @classmethod
    def from_orm_model(cls, obj: Any) -> "SpatialFeatureOut":
        return cls.model_validate(obj)


class HistogramBin(BaseModel):
    midpoint: float
    count: int


class HistogramOut(BaseModel):
    index_name: str
    counts: List[int]
    bin_edges: List[float]
    bin_midpoints: List[float]
    total_pixels: int
    num_bins: int


class CompositeRequest(BaseModel):
    mode: str = "RGB"          # "RGB" | "FALSE_COLOR" | "SWIR"
    location_id: Optional[str] = None
