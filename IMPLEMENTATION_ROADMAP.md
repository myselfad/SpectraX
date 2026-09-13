# Implementation Roadmap

## Context
Based on the audit (2026-09-10), there is **no existing codebase**. This roadmap covers building the complete system from scratch, prioritized for a working SIH 2026 demo.

## Guiding Principle
**A real, working, honest end-to-end prototype** over architectural perfection.

---

## P0 — REQUIRED for Working SIH Prototype

### Phase 1: Project Scaffold + Environment ⏱️ ~1 hour
- [ ] Create project directory structure (`backend/`, `frontend/`)
- [ ] Initialize Python backend with FastAPI, dependencies (`requirements.txt`)
- [ ] Initialize React frontend with Vite (`package.json`)
- [ ] Create `.env` configuration
- [ ] Verify backend starts (`uvicorn`)
- [ ] Verify frontend starts (`npm run dev`)
- [ ] Verify frontend ↔ backend connectivity (health endpoint + CORS)

**Definition of Done:** Both services start and communicate. `GET /api/health` returns from frontend.

---

### Phase 2: Input + Preprocessing Pipeline ⏱️ ~2 hours
- [ ] Implement file upload API (`POST /api/upload`)
- [ ] Implement file validation (format, corruption, size limits)
- [ ] Implement metadata extraction (dimensions, bands, CRS, resolution) via rasterio
- [ ] Implement band detection and selection (RGB + NIR where available)
- [ ] Implement NoData handling
- [ ] Implement per-band normalization (min-max or percentile-based)
- [ ] Implement patch/tile generation with configurable overlap
- [ ] Implement tensor preparation (NumPy → PyTorch tensor)
- [ ] Create upload UI component with metadata display
- [ ] Create meaningful validation error messages
- [ ] Write preprocessing unit tests

**Definition of Done:** A valid GeoTIFF upload produces correctly shaped, normalized, model-ready tensor patches. Invalid files return clear errors.

---

### Phase 3: Super-Resolution Engine ⏱️ ~2 hours
- [ ] Implement SR model architecture (EDSR baseline — proven, lightweight, no pretrained weight dependency issues)
- [ ] Implement model with dropout layers (enabling future MC-Dropout)
- [ ] Create model loading/initialization logic
- [ ] Initialize with random weights for MVP (clearly documented)
- [ ] Implement inference pipeline (patches → model → output patches)
- [ ] Implement patch stitching with overlap blending
- [ ] Implement post-processing (denormalization, clipping)
- [ ] Implement correct output dimension handling (input × scale_factor)
- [ ] Handle device selection (CUDA if available, else CPU)
- [ ] Write model inference tests (shape correctness, deterministic output)

**MVP Model Decision:**
- Architecture: EDSR-style residual network (clean, well-understood)
- Input channels: 3 (RGB) for MVP; NIR handled separately via bicubic
- Scale factor: 2× or 4× (configurable)
- Dropout: Included in architecture for MC-Dropout compatibility
- Weights: Random initialization → produces real but untrained SR output
- This is clearly labeled as "MVP Baseline" — not claimed as a trained research model

**Definition of Done:** Model loads, runs real inference, produces correctly shaped output. Output is genuine model computation, not bicubic upsampling disguised as AI.

---

### Phase 4: Processing API + Status ⏱️ ~1.5 hours
- [ ] Implement processing endpoint (`POST /api/process`)
- [ ] Implement job tracking with unique IDs
- [ ] Implement processing status endpoint (`GET /api/status/{job_id}`)
- [ ] Implement background processing (async task or in-process with status updates)
- [ ] Implement results endpoint (`GET /api/results/{job_id}`)
- [ ] Connect: upload → validate → preprocess → inference → reconstruct → store results
- [ ] Implement proper error propagation through pipeline
- [ ] Write API integration tests

**Definition of Done:** `POST /api/process` triggers the full pipeline. Status polling works. Results are retrievable.

---

### Phase 5: Full Frontend Integration ⏱️ ~2.5 hours
- [ ] Build landing/dashboard page with project identity
- [ ] Build upload component with drag-and-drop + file selection
- [ ] Build metadata display panel (only shows real extracted data)
- [ ] Build processing configuration panel (scale factor, bands)
- [ ] Build processing progress visualization (real status from backend)
- [ ] Build results dashboard layout
- [ ] Implement original image display
- [ ] Implement SR output display
- [ ] Implement before/after comparison (slider or side-by-side)
- [ ] Implement processing info panel (model, time, dimensions, scale)
- [ ] Build error display components
- [ ] Connect all components to backend API

**Definition of Done:** Complete user flow works: land → upload → configure → process → view results.

---

### Phase 6: Demo Sample + End-to-End Test ⏱️ ~1 hour
- [ ] Create/obtain a known-good sample GeoTIFF (multi-band, georeferenced)
- [ ] Create a simpler fallback PNG sample for basic testing
- [ ] Run full pipeline with demo sample
- [ ] Verify all displayed information is genuine
- [ ] Fix any pipeline failures
- [ ] Document demo flow

**Definition of Done:** A judge can see a complete demo without errors.

---

## P1 — IMPORTANT (Reliability + Validation)

### Phase 7: Uncertainty / Reliability Module ⏱️ ~1.5 hours
- [ ] Implement MC-Dropout inference (multiple forward passes with dropout enabled)
- [ ] Compute mean prediction from stochastic passes
- [ ] Compute pixel-wise variance/standard deviation
- [ ] Generate uncertainty heatmap (colormap visualization)
- [ ] Add uncertainty to results API
- [ ] Display uncertainty map in frontend (with explanation)
- [ ] Add configuration for number of MC-Dropout passes
- [ ] Write uncertainty tests

**Prerequisite:** Model architecture includes dropout layers (designed in Phase 3).

**Definition of Done:** Uncertainty map is mathematically derived from model stochasticity, not decorative.

---

### Phase 8: Validation Metrics ⏱️ ~1.5 hours
- [ ] Implement PSNR calculation (only with valid reference)
- [ ] Implement SSIM calculation (only with valid reference)
- [ ] Implement SAM calculation (spectral angle mapper, multispectral)
- [ ] Implement ERGAS calculation (relative global error)
- [ ] Implement observation consistency (SR → degrade → compare with LR input)
- [ ] Add validation results to API
- [ ] Display metrics in frontend (clearly labeled, only when valid)
- [ ] Display observation consistency separately from reference-based metrics
- [ ] Write validation metric tests (known-value verification)

**Definition of Done:** Every displayed metric has a valid mathematical interpretation. No metrics shown without valid computation.

---

### Phase 9: Export ⏱️ ~0.5 hours
- [ ] Implement SR output download (GeoTIFF or PNG)
- [ ] Implement uncertainty map download (if computed)
- [ ] Implement metrics report download (JSON)
- [ ] Add export buttons to frontend (only for genuinely generated files)
- [ ] Write export tests

**Definition of Done:** Users can download actual processing outputs.

---

## P2 — ENHANCEMENTS (Post-MVP)

### Phase 10: Polish + Advanced Features
- [ ] Zoom/pan capability on result images
- [ ] Better geospatial visualization (map overlay if feasible)
- [ ] Responsive design refinement
- [ ] Batch processing support
- [ ] Pretrained model weights (from actual training on satellite data)
- [ ] True 4-band (RGB+NIR) joint super-resolution model
- [ ] Docker deployment configuration
- [ ] Performance optimization
- [ ] Additional satellite format support

---

## Implementation Order Summary

```
Phase 1: Scaffold        ──► Both services start
Phase 2: Input/Preproc   ──► Valid input → model-ready data
Phase 3: SR Engine       ──► Real model inference works
Phase 4: Processing API  ──► End-to-end pipeline via API
Phase 5: Frontend        ──► Complete UI flow
Phase 6: Demo Sample     ──► Working demo
Phase 7: Uncertainty     ──► Reliability maps (P1)
Phase 8: Validation      ──► Scientific metrics (P1)
Phase 9: Export          ──► Download outputs (P1)
```

---

## Current MVP Model vs. Intended Research Model

| Aspect | MVP Baseline | Intended Research Model |
|--------|-------------|------------------------|
| Architecture | EDSR-style residual CNN | SwinIR-inspired transformer |
| Input channels | 3 (RGB) | 4 (B, G, R, NIR) |
| NIR handling | Bicubic upsampling (separate) | Joint spectral processing |
| Weights | Random initialization | Trained on satellite data |
| Dropout | Included (for MC-Dropout) | Integrated for uncertainty |
| Scale factor | 2× / 4× | Configurable |
| Output quality | Untrained (structural, not sharp) | Trained enhancement |
| Uncertainty | MC-Dropout (functional) | MC-Dropout (calibrated) |

**This distinction is clearly communicated in the UI and documentation.**

---

## Estimated Total Implementation Time

| Priority | Phases | Estimated Time |
|----------|--------|---------------|
| P0 | Phases 1–6 | ~10 hours |
| P1 | Phases 7–9 | ~3.5 hours |
| P2 | Phase 10 | Variable |
| **Total MVP (P0+P1)** | **Phases 1–9** | **~13.5 hours** |

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| No trained model weights | Use EDSR with random weights; clearly label as MVP baseline |
| GDAL installation issues | Use rasterio (Python wrapper); fall back to PIL for basic formats |
| Large GeoTIFF memory issues | Patch-based processing with configurable tile size |
| No GPU available | CPU inference works (slower); design for device-agnostic execution |
| No Sentinel-2 sample available | Generate synthetic multi-band GeoTIFF; also support standard image formats as fallback |
