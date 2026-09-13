# Setup Guide

## Important
Exact commands and versions must be filled after repository audit. Do not invent versions.

## Expected Components
- Node.js frontend environment
- Python backend environment
- FastAPI
- PyTorch
- Rasterio/GDAL
- Model weights
# System Setup Guide

## Requirements

- Python 3.9+
- Node.js 18+
- PyTorch (CPU or CUDA)

## 1. Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Download the pretrained SwinIR model if not already present:
```bash
mkdir -p weights
curl -L -o weights/swinir_classical_sr_x4.pth "https://github.com/JingyunLiang/SwinIR/releases/download/v0.0/001_classicalSR_DIV2K_s48w8_SwinIR-M_x4.pth"
```

Start the FastAPI server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The application will be available at `http://localhost:5173/`.

## 3. Demo Data

Generate synthetic sample data for testing:
```bash
cd backend
source venv/bin/activate
python scripts/create_sample_data.py
```
This will create a 4-band GeoTIFF and a 3-band PNG in `backend/data/`.

## Environment Variables To Verify
- MODEL_PATH
- DATA_DIRECTORY
- OUTPUT_DIRECTORY
- BACKEND_HOST
- BACKEND_PORT
- FRONTEND_API_URL
- Any storage/database credentials if actually used

Do not add variables that are not used by the actual codebase.
