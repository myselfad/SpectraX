# Testing Report

## Current Status
⚪ Existing automated/manual tests require repository audit.

## Required Test Areas

### Input Validation
- Unsupported format
- Corrupt file
- Missing required bands
- NoData handling
- Invalid metadata

### Preprocessing
- Normalization
- Patch generation
- Overlap
- Tensor shapes

### Model
- Model loading
- Inference
- Output dimensions
- Deterministic/stochastic behavior where applicable

### Uncertainty
- Multiple stochastic passes
- Mean prediction
- Variance output
- Heatmap generation

### Validation
- Metrics with valid reference
- No metric calculation without valid reference
- Observation consistency

### API
- Success responses
- Validation errors
- Processing failures

### Frontend
- Upload
- Status display
- Error messages
- Results rendering

### End-to-End
Known-good sample:
Upload → preprocess → inference → results → validation → export.

## Reporting Format
| Test | Expected Result | Actual Result | Status | Evidence |
|---|---|---|---|---|
