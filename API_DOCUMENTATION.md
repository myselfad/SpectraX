# API Documentation

## Status
Actual API endpoints require repository audit.

The following is a proposed structure and must not be presented as existing until verified.

## [PROPOSED] POST /api/upload
Purpose: Upload supported imagery.

## [PROPOSED] POST /api/validate
Purpose: Validate metadata, bands, CRS and file compatibility.

## [PROPOSED] POST /api/process
Purpose: Execute preprocessing and SR pipeline.

## [PROPOSED] GET /api/status/{job_id}
Purpose: Retrieve processing progress.

## [PROPOSED] GET /api/results/{job_id}
Purpose: Retrieve output metadata and visualization references.

## [PROPOSED] GET /api/metrics/{job_id}
Purpose: Retrieve genuinely calculated metrics.

## [PROPOSED] GET /api/export/{job_id}
Purpose: Export available outputs.

## API Principles
- Use typed request/response schemas.
- Return meaningful validation errors.
- Never return fake metrics.
- Separate processing failures from input validation failures.
- Preserve enough metadata to interpret geospatial output.
