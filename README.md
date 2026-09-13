# SpectraX: Reliability-Aware Multispectral Satellite Super Resolution

![SpectraX Logo](docs/assets/test.png) <!-- Update with actual logo if available -->

SpectraX is a cutting-edge platform designed for **multispectral satellite imagery super-resolution**. Built for the SIH 2026 challenge, it leverages the state-of-the-art **SwinIR** (Swin Transformer for Image Restoration) architecture alongside **Monte Carlo Dropout** to not only enhance the spatial resolution of satellite imagery but also provide critical uncertainty estimation.

## 🌟 Key Features

* **Advanced Super-Resolution:** Utilizes a classical SwinIR model to upscale satellite imagery (2x, 4x) while preserving fine structural details and multispectral consistency.
* **Uncertainty Estimation:** Integrates Monte Carlo Dropout to generate pixel-wise uncertainty maps, providing a reliability score for the AI-generated pixels. This is crucial for scientific and defense applications where trust in AI output is mandatory.
* **Multispectral Support:** Natively handles 4-band (RGB + Near Infrared) GeoTIFFs, common in Sentinel and Landsat data.
* **Interactive Dashboard:** A responsive React-based frontend allows users to upload imagery, run inference, and compare original vs. enhanced imagery side-by-side.
* **Robust Backend API:** A fast, asynchronous FastAPI backend handles intensive processing, job queuing, and AWS S3 integration.
* **Cloud Ready:** Deploys seamlessly to AWS EC2 with automatic hardware detection (CUDA/MPS/CPU).

## 🚀 Quick Start (Local Setup)

The application is built to run entirely offline on your local machine, automatically utilizing your GPU if available (NVIDIA CUDA or Apple Silicon MPS).

### Prerequisites
* Python 3.10+
* Node.js 18+
* (Optional) AWS account for S3 storage fallback

### 1. Backend Setup (FastAPI + PyTorch)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start the server (runs on http://localhost:8000)
python run.py
```

### 2. Frontend Setup (React + Vite)

Open a new terminal window:

```bash
cd frontend
npm install
npm run dev
```
Access the dashboard at `http://localhost:5173`.

## 📚 Documentation

Detailed documentation has been organized into the `docs/` folder:

* [Project Architecture](docs/project_architecture.md) - High-level system design.
* [Backend Implementation](docs/backend_implementation.md) - Details on the FastAPI and PyTorch pipeline.
* [Frontend Implementation](docs/frontend_implementation.md) - React UI component structure.
* [Setup & Demo Guide](docs/setup_guide.md) - Extended installation and demo instructions.

## 🧠 ML Architecture

* **Base Model:** SwinIR (Swin Transformer)
* **Upscaling:** Classical Super Resolution (x2, x4)
* **Uncertainty:** Monte Carlo (MC) Dropout (10-50 passes)
* **Framework:** PyTorch
* **Device Support:** Auto-detects `cuda`, `mps` (Apple Silicon), or `cpu`.

## 🔒 Security & AWS

AWS integration is strictly handled via the backend. S3 buckets are configured with **Block Public Access** and **AES-256 Encryption**. No credentials are ever exposed to the frontend. Ensure your `.env` file is properly configured if using cloud storage.

---
*Developed for Smart India Hackathon (SIH) 2026*
