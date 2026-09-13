import asyncio
import threading
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.schemas.process import ProcessRequest, ProcessResponse, StatusResponse, PipelineStep
from app.api.routes.upload import jobs
from app.services.pipeline import PipelineRunner
from app.core.config import settings

router = APIRouter()

def _run_pipeline_sync(runner: PipelineRunner):
    """Run the pipeline synchronously in a background thread."""
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(runner.run())
    finally:
        loop.close()

@router.post("/process", response_model=ProcessResponse)
async def process_image(req: ProcessRequest):
    if req.job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job_data = jobs[req.job_id]
    job_data['request'] = req.model_dump()
    job_data['status'] = 'processing'
    job_data['steps'] = []
    job_data['progress_percent'] = 0.0
    
    runner = PipelineRunner(req.job_id, job_data, settings)
    
    # Run in a separate thread so it does NOT block the event loop.
    # This allows /api/status and other endpoints to remain responsive
    # while heavy PyTorch inference runs.
    thread = threading.Thread(target=_run_pipeline_sync, args=(runner,), daemon=True)
    thread.start()
    
    print(f"[PROCESS] pipeline started in thread for job {req.job_id}")
    
    return ProcessResponse(job_id=req.job_id, status='processing')

@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job_data = jobs[job_id]
    
    steps = [PipelineStep(**s) for s in job_data.get('steps', [])]
    
    return StatusResponse(
        job_id=job_id,
        status=job_data.get('status', 'unknown'),
        current_step=job_data.get('current_step'),
        steps=steps,
        progress_percent=job_data.get('progress_percent', 0.0),
        error=job_data.get('error'),
        started_at=job_data.get('started_at'),
        completed_at=job_data.get('completed_at')
    )
