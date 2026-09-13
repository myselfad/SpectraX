from fastapi import APIRouter, HTTPException
from app.schemas.results import ResultsResponse, MetricsResult, ProcessingInfo, BandInfo
from app.api.routes.upload import jobs

router = APIRouter()

@router.get("/results/{job_id}", response_model=ResultsResponse)
async def get_results(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job_data = jobs[job_id]
    if job_data.get('status') not in ('completed', 'failed'):
        raise HTTPException(status_code=400, detail=f"Job status: {job_data.get('status', 'unknown')}. Not yet completed.")
        
    res = job_data.get('results', {})
    
    metrics = None
    if 'metrics' in res and res['metrics']:
        raw_metrics = res['metrics']
        metrics_dict = {
            'observation_consistency': raw_metrics.get('observation_consistency'),
            'reference_metrics': raw_metrics.get('reference_metrics'),
            'psnr': raw_metrics.get('observation_consistency', {}).get('consistency_psnr', None),
            'ssim': raw_metrics.get('observation_consistency', {}).get('consistency_ssim', None),
            'spectral_error': raw_metrics.get('reference_metrics', {}).get('sam', None)
        }
        metrics = MetricsResult(**metrics_dict)
    
    processing_info = None
    if 'processing_info' in res and res['processing_info']:
        processing_info = ProcessingInfo(**res['processing_info'])
    
    band_info = None
    if 'band_info' in res and res['band_info']:
        band_info = [BandInfo(**b) for b in res['band_info']]

    # Phase 10 requested payload structure extraction
    model_obj = {
        "name": processing_info.model_name if processing_info else "SwinIR-M",
        "mode": "deep_learning"
    }
    input_obj = {
        "width": processing_info.input_width if processing_info else 0,
        "height": processing_info.input_height if processing_info else 0,
        "bands": processing_info.input_bands if processing_info else 4
    }
    output_obj = {
        "width": processing_info.output_width if processing_info else 0,
        "height": processing_info.output_height if processing_info else 0,
        "scale_factor": processing_info.scale_factor if processing_info else 4
    }
    
    unc_result = job_data.get('uncertainty_result') or {}
    u_stats = unc_result.get('uncertainty_stats', {})
    r_stats = unc_result.get('reliability_stats', {})
    
    uncertainty_obj = {
        "monte_carlo_passes": job_data.get('request', {}).get('uncertainty_passes', 10),
        "mean_uncertainty": u_stats.get('mean', 0.0)
    }
    reliability_obj = {
        "mean_score": r_stats.get('mean_score', 0.0),
        "high_reliability_percentage": r_stats.get('high_reliability_percentage', 0.0)
    }
    outputs_obj = {
        "super_resolved": res.get('sr_image_url', f"/api/files/{job_id}/sr_output.png"),
        "uncertainty_map": res.get('uncertainty_map_url', f"/api/files/{job_id}/uncertainty_map.png"),
        "reliability_map": f"/api/files/{job_id}/reliability_map.png"
    }
    
    return ResultsResponse(
        job_id=job_id,
        status=job_data['status'],
        original_image_url=res.get('original_image_url', f"/api/files/{job_id}/original.png"),
        sr_image_url=res.get('sr_image_url', f"/api/files/{job_id}/sr_output.png"),
        sr_bands_url=res.get('sr_bands_url'),
        uncertainty_map_url=res.get('uncertainty_map_url'),
        metrics=metrics,
        processing_info=processing_info,
        band_info=band_info,
        export_available=res.get('export_available', []),
        model=model_obj,
        input=input_obj,
        output=output_obj,
        uncertainty=uncertainty_obj,
        reliability=reliability_obj,
        outputs=outputs_obj
    )
