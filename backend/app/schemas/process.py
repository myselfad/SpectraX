from pydantic import BaseModel
from typing import Optional

class ProcessRequest(BaseModel):
    job_id: str
    scale_factor: int = 4
    selected_bands: list[str] = ['red','green','blue','nir']
    uncertainty_passes: int = 10
    processing_mode: str = 'standard'

class ProcessResponse(BaseModel):
    job_id: str
    status: str

class PipelineStep(BaseModel):
    name: str
    status: str = 'pending'
    duration_ms: Optional[float] = None
    message: Optional[str] = None

class StatusResponse(BaseModel):
    job_id: str
    status: str
    current_step: Optional[str] = None
    steps: list[PipelineStep]
    progress_percent: float
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
