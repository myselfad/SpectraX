from pydantic import BaseModel
from typing import Optional

class UploadResponse(BaseModel):
    job_id: str
    filename: str
    file_type: str
    width: int
    height: int
    num_bands: int
    band_names: list[str]
    crs: Optional[str] = None
    spatial_resolution: Optional[dict] = None
    nodata_value: Optional[float] = None
    file_size_bytes: int

class ValidationError(BaseModel):
    field: str
    message: str
    code: str
