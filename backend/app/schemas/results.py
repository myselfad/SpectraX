from pydantic import BaseModel, ConfigDict
from typing import Optional, Any

class BandInfo(BaseModel):
    name: str
    method: str = 'swinir_sr'
    description: str

class ProcessingInfo(BaseModel):
    model_name: str
    model_type: str
    scale_factor: int
    input_width: int
    input_height: int
    output_width: int
    output_height: int
    input_bands: int
    processing_time_seconds: float
    device: str
    uncertainty_passes: Optional[int] = None
    nir_method: str

class MetricsResult(BaseModel):
    model_config = ConfigDict(extra='allow')
    observation_consistency: Optional[dict] = None
    reference_metrics: Optional[dict] = None

class ResultsResponse(BaseModel):
    model_config = ConfigDict(extra='allow')
    job_id: str
    status: str
    original_image_url: str
    sr_image_url: str
    sr_bands_url: Optional[dict[str,str]] = None
    uncertainty_map_url: Optional[str] = None
    metrics: Optional[MetricsResult] = None
    processing_info: Optional[ProcessingInfo] = None
    band_info: Optional[list[BandInfo]] = None
    export_available: list[str]
