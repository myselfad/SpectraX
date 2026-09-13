import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import torch

from app.core.config import settings
from app.api.routes import upload, process, results, export
from app.super_resolution.model import ModelManager

app = FastAPI(
    title="SpectraX SR API",
    description="Backend for the SIH 2026 Reliability-Aware Multispectral Satellite Super Resolution project."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/api/files", StaticFiles(directory=settings.OUTPUT_DIR), name="files")

app.include_router(upload.router, prefix="/api")
app.include_router(process.router, prefix="/api")
app.include_router(results.router, prefix="/api")
app.include_router(export.router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Init model manager
    mm = ModelManager.get_instance()
    # Try to load model
    try:
        mm.load_model(settings.MODEL_PATH)
        print(f"Model loaded: {mm.is_loaded} on {mm.device}")
    except Exception as e:
        print(f"Model init failed: {e}")

@app.get("/api/health")
async def health_check():
    mm = ModelManager.get_instance()
    return {
        "status": "healthy",
        "model_loaded": mm.is_loaded,
        "device": str(mm.device),
        "version": "1.0.0",
        "upscale_factor": settings.DEFAULT_SCALE_FACTOR
    }
