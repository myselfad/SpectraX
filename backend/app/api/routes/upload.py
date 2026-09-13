import os
import uuid
import shutil
import traceback
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.config import settings
from app.schemas.upload import UploadResponse
from app.preprocessing.validation import validate_file
from app.preprocessing.metadata import extract_metadata
from app.services.s3_storage import s3_storage

router = APIRouter()

jobs: dict[str, dict] = {}

@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    print(f"[UPLOAD] === REQUEST RECEIVED ===")
    print(f"[UPLOAD] filename: {file.filename}")
    print(f"[UPLOAD] content_type: {file.content_type}")
    
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(settings.UPLOAD_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    filepath = os.path.join(job_dir, f"original_{file.filename}")
    print(f"[UPLOAD] saving to: {filepath}")
    
    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        err = traceback.format_exc()
        with open("last_error.log", "w") as f: f.write(err)
        print(f"[UPLOAD] SAVE FAILED: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}\n{err}")
    
    saved_size = os.path.getsize(filepath)
    print(f"[UPLOAD] file saved, size: {saved_size} bytes, exists: {os.path.exists(filepath)}")
    
    print(f"[UPLOAD] running validation...")
    try:
        validation_res = validate_file(filepath)
        print(f"[UPLOAD] validation result: valid={validation_res['is_valid']}, type={validation_res['file_type']}")
    except Exception as e:
        err = traceback.format_exc()
        with open("last_error.log", "w") as f: f.write(err)
        print(f"[UPLOAD] VALIDATION CRASHED: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}\n{err}")

    if not validation_res['is_valid']:
        print(f"[UPLOAD] file invalid: {validation_res['errors']}")
        raise HTTPException(status_code=400, detail=f"Invalid file: {validation_res['errors']}")
    
    print(f"[UPLOAD] extracting metadata...")
    try:
        metadata = extract_metadata(filepath)
        print(f"[UPLOAD] metadata extracted: width={metadata.get('width')}, height={metadata.get('height')}, bands={metadata.get('num_bands')}")
    except Exception as e:
        err = traceback.format_exc()
        with open("last_error.log", "w") as f: f.write(err)
        print(f"[UPLOAD] METADATA EXTRACTION CRASHED: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Metadata extraction error: {str(e)}\n{err}")
    
    file_size = os.path.getsize(filepath)
    
    # Upload to AWS S3 if enabled (non-blocking / graceful fallback)
    s3_info = {}
    if s3_storage.is_available():
        try:
            s3_info = s3_storage.upload_job_file(
                job_id=job_id,
                local_path=filepath,
                filename=f"original_{file.filename}",
                category="uploads"
            )
            print(f"[UPLOAD] Uploaded raw file to S3: {s3_info.get('s3_uri')}")
        except Exception as e:
            print(f"[UPLOAD] Non-fatal S3 upload warning: {e}")
    
    job_info = {
        'job_id': job_id,
        'filename': file.filename,
        'filepath': filepath,
        'metadata': metadata,
        'status': 'uploaded',
        's3': s3_info
    }
    jobs[job_id] = job_info
    
    print(f"[UPLOAD] building response...")
    try:
        response = UploadResponse(
            job_id=job_id,
            filename=file.filename,
            file_type=validation_res['file_type'],
            width=metadata.get('width', 0),
            height=metadata.get('height', 0),
            num_bands=metadata.get('num_bands', 0),
            band_names=metadata.get('band_names', []),
            crs=metadata.get('crs'),
            spatial_resolution=metadata.get('spatial_resolution'),
            nodata_value=metadata.get('nodata'),
            file_size_bytes=file_size
        )
        print(f"[UPLOAD] === SENDING RESPONSE === job_id={job_id}")
        return response
    except Exception as e:
        err = traceback.format_exc()
        with open("last_error.log", "w") as f: f.write(err)
        print(f"[UPLOAD] RESPONSE BUILD FAILED: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Response error: {str(e)}\n{err}")
