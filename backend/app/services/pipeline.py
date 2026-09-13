"""Main processing pipeline orchestrator.

Coordinates the complete satellite image super-resolution workflow:
Upload → Validate → Preprocess → SR Inference → Uncertainty → Validation → Output
"""

import os
import time
import json
import traceback
import numpy as np
from app.core.config import Settings, settings
from app.preprocessing.validation import validate_file
from app.preprocessing.metadata import extract_metadata
from app.preprocessing.bands import select_bands, detect_bands
from app.preprocessing.normalization import normalize_for_model
from app.super_resolution.model import ModelManager
from app.super_resolution.inference import run_sr_inference
from app.super_resolution.postprocess import postprocess_sr_output, create_output_geotiff
from app.uncertainty.mc_dropout import run_mc_dropout
from app.uncertainty.visualization import save_uncertainty_visualization
from app.validation.consistency import calculate_observation_consistency
from app.utils.image import save_visualization, create_comparison_image, save_rgb_preview
from app.utils.io import read_image
from app.services.s3_storage import s3_storage


class PipelineRunner:
    """Orchestrates the complete SR processing pipeline.
    
    Each pipeline step updates the shared job_data dict in real-time,
    enabling the frontend to poll for progress.
    """
    
    def __init__(self, job_id: str, job_data: dict, config: Settings):
        self.job_id = job_id
        self.job_data = job_data
        self.config = config
        self.output_dir = os.path.join(config.OUTPUT_DIR, job_id)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Pipeline state
        self.image_data = None      # Raw image data (CHW)
        self.metadata = None        # Image metadata dict
        self.bands = None           # Separated band dict
        self.rgb_normalized = None  # Normalized RGB array (HWC, [0,1])
        self.nir_normalized = None  # Normalized NIR band or None
        self.norm_info = None       # Normalization parameters
        self.sr_output = None       # SR RGB output
        self.sr_postprocessed = None  # Post-processed output dict
        self.uncertainty_result = None
        self.consistency_result = None
        self.start_time = None
    
    def _update_step(self, name: str, status: str, message: str = None, duration_ms: float = None):
        """Update pipeline step status for frontend polling."""
        step = next((s for s in self.job_data.get('steps', []) if s['name'] == name), None)
        if not step:
            step = {'name': name, 'status': status, 'message': message, 'duration_ms': duration_ms}
            if 'steps' not in self.job_data:
                self.job_data['steps'] = []
            self.job_data['steps'].append(step)
        else:
            step['status'] = status
            step['message'] = message
            if duration_ms is not None:
                step['duration_ms'] = duration_ms
        
        self.job_data['current_step'] = name
        
        # Update progress based on completed steps
        total_steps = 8
        completed = sum(1 for s in self.job_data['steps'] if s['status'] == 'completed')
        self.job_data['progress_percent'] = min(100.0, (completed / total_steps) * 100)
    
    async def run(self):
        """Execute the complete processing pipeline."""
        self.start_time = time.time()
        self.job_data['started_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        
        pipeline_steps = [
            ('input_validation', self._validate_input),
            ('metadata_extraction', self._extract_metadata),
            ('band_selection', self._select_bands),
            ('preprocessing', self._preprocess),
            ('super_resolution', self._run_sr),
            ('uncertainty_estimation', self._run_uncertainty),
            ('validation', self._run_validation),
            ('output_generation', self._generate_outputs),
        ]
        
        try:
            for step_name, step_fn in pipeline_steps:
                self._update_step(step_name, 'running')
                step_start = time.time()
                try:
                    step_fn()
                    duration = (time.time() - step_start) * 1000
                    self._update_step(step_name, 'completed', duration_ms=round(duration, 1))
                except Exception as e:
                    duration = (time.time() - step_start) * 1000
                    error_msg = f"{type(e).__name__}: {str(e)}"
                    self._update_step(step_name, 'failed', message=error_msg, duration_ms=round(duration, 1))
                    raise
            
            self.job_data['status'] = 'completed'
            self.job_data['completed_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            self.job_data['progress_percent'] = 100.0
            
        except Exception as e:
            self.job_data['status'] = 'failed'
            self.job_data['error'] = f"{type(e).__name__}: {str(e)}"
            traceback.print_exc()
    
    def _validate_input(self):
        """Step 1: Validate the uploaded file."""
        filepath = self.job_data.get('filepath')
        if not filepath or not os.path.exists(filepath):
            raise FileNotFoundError(f"Upload file not found: {filepath}")
        
        validation = validate_file(filepath)
        if not validation['is_valid']:
            errors = '; '.join(validation.get('errors', ['Unknown validation error']))
            raise ValueError(f"Input validation failed: {errors}")
        
        self.job_data['validation'] = validation
    
    def _extract_metadata(self):
        """Step 2: Extract metadata from the image."""
        filepath = self.job_data.get('filepath')
        self.image_data, self.metadata = read_image(filepath)
        self.job_data['metadata'] = {
            k: v for k, v in self.metadata.items() 
            if k not in ('filepath',) and not isinstance(v, np.ndarray)
        }
    
    def _select_bands(self):
        """Step 3: Detect and select bands (RGB + NIR)."""
        # image_data is CHW format
        request = self.job_data.get('request', {})
        selected = request.get('selected_bands', ['red', 'green', 'blue', 'nir'])
        
        band_info = detect_bands(self.image_data, self.metadata)
        self.bands = select_bands(self.image_data, band_info, selected)
        
        self.job_data['detected_bands'] = list(self.bands.keys())
    
    def _preprocess(self):
        """Step 4: Normalize bands and prepare for model."""
        self.rgb_normalized, self.norm_info = normalize_for_model(self.bands)
        self.nir_normalized = self.norm_info.get('nir_data')
        
        self.job_data['preprocessing'] = {
            'normalized_shape': list(self.rgb_normalized.shape),
            'has_nir': self.norm_info['has_nir'],
            'band_order': self.norm_info['band_order'],
        }
    
    def _run_sr(self):
        """Step 5: Run super-resolution inference."""
        mm = ModelManager.get_instance()
        if mm.model is None:
            raise RuntimeError("SR model not loaded. Check MODEL_PATH in configuration.")
        
        request = self.job_data.get('request', {})
        scale = request.get('scale_factor', 4)
        tile_size = self.config.DEFAULT_PATCH_SIZE
        overlap = self.config.DEFAULT_PATCH_OVERLAP
        
        # Run SR on RGB
        self.sr_output = run_sr_inference(
            mm, self.rgb_normalized,
            tile_size=tile_size, overlap=overlap
        )
        
        # SwinIR model is fixed to 4x. Downsample if 2x was requested.
        if scale != 4:
            import cv2
            h, w, c = self.sr_output.shape
            new_h = int(h * scale / 4)
            new_w = int(w * scale / 4)
            self.sr_output = cv2.resize(self.sr_output, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # Post-process (clip RGB, upscale NIR via bicubic)
        self.sr_postprocessed = postprocess_sr_output(
            self.sr_output, self.nir_normalized, scale
        )
        
        self.job_data['sr_info'] = {
            'input_shape': list(self.rgb_normalized.shape),
            'output_shape': list(self.sr_output.shape),
            'scale_factor': scale,
            'model_pretrained': mm.is_loaded,
        }
    
    def _run_uncertainty(self):
        """Step 6: Run MC-Dropout uncertainty estimation."""
        mm = ModelManager.get_instance()
        request = self.job_data.get('request', {})
        num_passes = request.get('uncertainty_passes', self.config.DEFAULT_UNCERTAINTY_PASSES)
        scale = request.get('scale_factor', 4)
        
        if mm.model is None:
            self._update_step('uncertainty_estimation', 'completed',
                             message='Skipped: model not available')
            return
        
        try:
            self.uncertainty_result = run_mc_dropout(
                model_manager=mm, 
                image_rgb=self.rgb_normalized, 
                num_passes=num_passes, 
                target_scale=scale, 
                tile_size=self.config.DEFAULT_PATCH_SIZE, 
                overlap=self.config.DEFAULT_PATCH_OVERLAP
            )
        except Exception as e:
            # Non-fatal: uncertainty is important but shouldn't block results
            print(f"UNCERTAINTY ERROR: {e}")
            self.uncertainty_result = None
            self._update_step('uncertainty_estimation', 'completed',
                             message=f'Uncertainty estimation failed: {str(e)}. Results generated without uncertainty.')
    
    def _run_validation(self):
        """Step 7: Run observation consistency validation."""
        if self.sr_output is None:
            return
        
        request = self.job_data.get('request', {})
        scale = request.get('scale_factor', 4)
        
        try:
            self.consistency_result = calculate_observation_consistency(
                self.sr_output, self.rgb_normalized, scale
            )
        except Exception as e:
            self.consistency_result = None
            self._update_step('validation', 'completed',
                             message=f'Consistency validation failed: {str(e)}')
    
    def _generate_outputs(self):
        """Step 8: Generate output files and results."""
        request = self.job_data.get('request', {})
        scale = request.get('scale_factor', 4)
        mm = ModelManager.get_instance()
        
        export_available = []
        
        # Save original RGB preview
        original_path = os.path.join(self.output_dir, 'original.png')
        save_rgb_preview(self.rgb_normalized, original_path)
        
        # Save SR RGB output
        sr_rgb = self.sr_postprocessed['rgb']
        sr_path = os.path.join(self.output_dir, 'sr_output.png')
        save_visualization(sr_rgb, sr_path)
        export_available.append('sr_image')
        
        # Save comparison image
        comparison_path = os.path.join(self.output_dir, 'comparison.png')
        create_comparison_image(self.rgb_normalized, sr_rgb, comparison_path)
        
        # Save GeoTIFF output if input was GeoTIFF
        if self.metadata.get('file_type') == 'geotiff':
            geotiff_path = os.path.join(self.output_dir, 'sr_output.tif')
            self.metadata['_scale_factor'] = scale
            try:
                create_output_geotiff(self.sr_postprocessed, self.metadata, geotiff_path)
                export_available.append('sr_geotiff')
            except Exception as e:
                print(f"GeoTIFF output failed: {e}")
        
        uncertainty_map_url = None
        reliability_map_url = None
        if self.uncertainty_result:
            from app.uncertainty.visualization import save_uncertainty_visualization, save_heatmap_visualization
            
            unc_path = os.path.join(self.output_dir, 'uncertainty_map.png')
            save_uncertainty_visualization(
                self.uncertainty_result['uncertainty_map'],
                unc_path,
                stats=self.uncertainty_result.get('uncertainty_stats')
            )
            uncertainty_map_url = f'/api/files/{self.job_id}/uncertainty_map.png'
            export_available.append('uncertainty_map')
            
            rel_path = os.path.join(self.output_dir, 'reliability_map.png')
            save_heatmap_visualization(
                self.uncertainty_result['reliability_map'],
                rel_path,
                colormap='viridis',
                title='Reliability Map (1 - Normalized Uncertainty)',
                cbar_label='Reliability Score',
                stats=None
            )
            reliability_map_url = f'/api/files/{self.job_id}/reliability_map.png'
            export_available.append('reliability_map')
        
        # Build processing info
        processing_time = time.time() - self.start_time if self.start_time else 0
        
        processing_info = {
            'model_name': 'SwinIR-M Classical SR' if mm.is_loaded else 'SwinIR-M (not pretrained)',
            'model_type': 'Swin Transformer (pretrained on DIV2K)' if mm.is_loaded else 'Swin Transformer',
            'scale_factor': scale,
            'input_width': self.rgb_normalized.shape[1],
            'input_height': self.rgb_normalized.shape[0],
            'output_width': sr_rgb.shape[1],
            'output_height': sr_rgb.shape[0],
            'input_bands': len(self.bands) if self.bands else 3,
            'processing_time_seconds': round(processing_time, 2),
            'device': str(mm.device) if mm.device else 'cpu',
            'uncertainty_passes': self.uncertainty_result['num_passes'] if self.uncertainty_result else None,
            'nir_method': 'bicubic_interpolation' if self.nir_normalized is not None else 'not_applicable',
        }
        
        # Build band info
        band_methods = self.sr_postprocessed.get('band_methods', {})
        band_info = []
        for name, info in band_methods.items():
            band_info.append({
                'name': name,
                'method': info['method'],
                'description': info['description'],
            })
        
        # Build metrics
        metrics = {}
        if self.consistency_result:
            metrics['observation_consistency'] = self.consistency_result
        if self.uncertainty_result:
            metrics['uncertainty_stats'] = self.uncertainty_result.get('uncertainty_stats')
            metrics['uncertainty_method'] = self.uncertainty_result.get('method_description')
        
        # Save metrics report JSON
        metrics_path = os.path.join(self.output_dir, 'metrics_report.json')
        metrics_report = {
            'job_id': self.job_id,
            'processing_info': processing_info,
            'band_info': band_info,
            'metrics': metrics,
            'prototype_notes': {
                'model': 'SwinIR-M pretrained on DIV2K for classical image super-resolution',
                'rgb_method': 'Genuine SwinIR transformer inference',
                'nir_method': 'Bicubic interpolation baseline (not AI super-resolved)' if self.nir_normalized is not None else 'No NIR band',
                'uncertainty_method': self.uncertainty_result.get('method', 'Not computed') if self.uncertainty_result else 'Not computed',
                'limitation': 'Prototype uses RGB-only SR model. NIR is upscaled via interpolation. Intended research model targets joint 4-band processing.',
            }
        }
        with open(metrics_path, 'w') as f:
            json.dump(metrics_report, f, indent=2, default=str)
        export_available.append('metrics_report')
        
        # Upload generated outputs to AWS S3 if enabled (non-blocking / graceful fallback)
        s3_outputs = {}
        if s3_storage.is_available():
            try:
                for fname in os.listdir(self.output_dir):
                    fpath = os.path.join(self.output_dir, fname)
                    if os.path.isfile(fpath):
                        upload_meta = s3_storage.upload_job_file(
                            job_id=self.job_id,
                            local_path=fpath,
                            filename=fname,
                            category="outputs"
                        )
                        s3_outputs[fname] = upload_meta
                print(f"[PIPELINE] Synced {len(s3_outputs)} output artifact(s) to S3 for job {self.job_id}")
            except Exception as e:
                print(f"[PIPELINE] Non-fatal S3 outputs upload warning: {e}")

        # Store results for API
        self.job_data['uncertainty_result'] = self.uncertainty_result
        self.job_data['results'] = {
            'original_image_url': f'/api/files/{self.job_id}/original.png',
            'sr_image_url': f'/api/files/{self.job_id}/sr_output.png',
            'comparison_url': f'/api/files/{self.job_id}/comparison.png',
            'uncertainty_map_url': uncertainty_map_url,
            'metrics': metrics,
            'processing_info': processing_info,
            'band_info': band_info,
            'export_available': export_available,
            's3': s3_outputs,
        }
