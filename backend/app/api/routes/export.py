import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.core.config import settings
from app.services.s3_storage import s3_storage

router = APIRouter()

@router.get("/export/{job_id}/{file_type}")
async def export_file(job_id: str, file_type: str):
    valid_types = {
        'sr_image': 'sr_output.png',
        'sr_geotiff': 'sr_output.tif',
        'uncertainty_map': 'uncertainty_map.png',
        'reliability_map': 'reliability_map.png',
        'metrics_report': 'metrics_report.json',
        'original': 'original.png',
        'comparison': 'comparison.png'
    }
    
    if file_type not in valid_types:
        raise HTTPException(status_code=400, detail="Invalid file type")
        
    filepath = os.path.join(settings.OUTPUT_DIR, job_id, valid_types[file_type])
    
    if not os.path.exists(filepath):
        # Graceful retrieval from AWS S3 if enabled
        if s3_storage.is_available():
            s3_key = f"outputs/{job_id}/{valid_types[file_type]}"
            downloaded = s3_storage.download_file(s3_key=s3_key, local_path=filepath)
            if not downloaded:
                raise HTTPException(status_code=404, detail="File not found locally or in S3")
        else:
            raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(filepath)
