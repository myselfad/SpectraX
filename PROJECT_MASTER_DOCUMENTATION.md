# SIH 2026 — Master Project Documentation

## 1. Project Identity
**Project:** Reliability-Aware Multispectral Satellite Super Resolution  
**Tagline:** Resolution without Reliability is not Intelligence.  
**Problem Statement ID:** 26142  
**Problem Statement:** Deep Learning Based Super Resolution Mapping (SRM) from Medium Resolution Satellite Imageries  
**Theme:** Space Technology  
**Category:** Software  
**Status:** IMPLEMENTED  
**Phase:** PROTOTYPE COMPLETE  
**Team:** SpectraX  

## 2. Project Summary
The project aims to transform medium-resolution multispectral satellite imagery into enhanced outputs while explicitly exposing uncertainty and validating reconstruction quality. The intended prototype focuses on Sentinel-2 imagery using RGB + NIR bands.

The intended value proposition is:

**Ordinary approach:** Input → Sharper Image  
**Our approach:** Input → Super-Resolved Image + Uncertainty + Validation

## 3. Core Objectives
### Primary
- Improve spatial detail of supported satellite imagery using deep learning.
- Preserve multispectral relationships across RGB + NIR.
- Provide uncertainty information rather than presenting generated detail as equally trustworthy.
- Provide measurable validation results.

### Prototype
- Accept supported satellite imagery / GeoTIFF input.
- Validate and preprocess input.
- Run genuine super-resolution inference.
- Visualize input and output.
- Produce scientifically honest validation results.
- Provide a working demonstration workflow.

## 4. Intended End-to-End Architecture
User
→ Frontend
→ Upload/API
→ Input Validation
→ GeoTIFF Reading
→ Band Selection
→ NoData Handling
→ Normalization
→ Geo-aware Tiling
→ Super-Resolution Inference
→ Patch Stitching
→ Uncertainty Estimation
→ Validation
→ Metrics
→ Results Dashboard
→ Export

## 5. Intended Technology Stack
| Layer | Intended Technology |
|---|---|
| Frontend | React + visualization/comparison components |
| Backend | Python + FastAPI |
| AI/ML | PyTorch |
| SR | SwinIR-inspired transformer backbone (intended research direction) |
| Uncertainty | Monte Carlo Dropout (intended method) |
| Geospatial | Rasterio + GDAL + NumPy |
| Optional image processing | OpenCV where required |
| Input/Output | GeoTIFF + derived visualizations + JSON metrics |
| Training | GPU-enabled cloud/institutional compute |

## 6. Intended Processing Pipeline
1. Upload supported satellite imagery.
2. Validate format, dimensions, CRS, bands and NoData.
3. Select Blue, Green, Red and NIR where supported.
4. Normalize selected data.
5. Split large imagery into overlapping patches.
6. Run super-resolution inference.
7. Stitch output patches while maintaining spatial alignment.
8. Run uncertainty estimation where technically supported.
9. Generate final SR output and uncertainty map.
10. Perform reference-based validation when valid ground truth exists.
11. Perform observation consistency validation where implemented.
12. Return visual results, metrics and exportable outputs.

## 7. Reliability Concept
### Spectral Preservation
RGB and NIR should be treated as related multispectral channels rather than four unrelated images.

### Uncertainty Awareness
The intended research approach is Monte Carlo Dropout:
multiple stochastic passes → prediction collection → mean prediction → pixel-wise variance/uncertainty.

### Observation Consistency
A reconstructed SR image can be degraded/downsampled and compared with the original observation. This is an observation-consistency check, not proof that every generated high-resolution detail is ground truth.

## 8. Validation
### Reference-based metrics
Use only when a valid reference exists:
- PSNR
- SSIM
- SAM
- ERGAS

### Observation consistency
SR output → controlled degradation/downsampling → comparison with original LR input.

## 9. Project Status Rule
This documentation distinguishes between:
- 🟢 Implemented
- 🟡 Partially implemented
- 🔴 Not implemented
- 🔵 Planned / intended
- ⚪ Needs confirmation

**Important:** The currently available SIH PRD/PPT describes intended architecture and prototype modules. It does not, by itself, prove that those modules are implemented in the current codebase.

## 10. Current Implementation Status
| Component | Status | Location / Details |
| :--- | :--- | :--- |
| **Backend Framework** | 🟢 IMPLEMENTED | FastAPI (`backend/app/`) |
| **Model Architecture** | 🟢 IMPLEMENTED | SwinIR-M PyTorch (`backend/app/super_resolution/swinir_arch.py`) |
| **Pretrained Weights** | 🟢 IMPLEMENTED | `swinir_classical_sr_x4.pth` downloaded |
| **GeoTIFF I/O** | 🟢 IMPLEMENTED | `backend/app/utils/io.py` using Rasterio |
| **Patch Tiling Engine** | 🟢 IMPLEMENTED | Overlap + blending (`backend/app/preprocessing/tiling.py`) |
| **MC-Dropout / Uncertainty**| 🟢 IMPLEMENTED | Stochastic depth passes (`backend/app/uncertainty/mc_dropout.py`) |
| **Frontend UI** | 🟢 IMPLEMENTED | React/Vite/Tailwind (`frontend/`) |
| **Status Endpoints** | 🟢 IMPLEMENTED | Real-time polling via pipeline runner |

- Existing tests
- Deployment configuration

## 11. Minimum SIH Demo
A successful prototype should demonstrate:
1. A known-good sample input.
2. Input validation.
3. Real preprocessing.
4. Genuine SR inference.
5. Before/after visualization.
6. Metrics only when genuinely calculated.
7. Uncertainty visualization only when technically valid.
8. Clear explanation of validation.
9. Robust error handling.
10. Reliable local demonstration without unnecessary external runtime dependencies.

## 12. Immediate Development Principle
Prioritize a complete, working and honest end-to-end workflow before adding advanced research complexity.

## 13. Source-of-Truth Update Rule
Whenever code changes:
1. Update implementation status.
2. Update APIs.
3. Update setup instructions.
4. Update tests.
5. Record architectural decisions.
6. Never mark a planned feature as implemented without verification.
