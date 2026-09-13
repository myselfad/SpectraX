"""Observation consistency validation.

Validates SR output by degrading it back to the original resolution
and comparing with the original low-resolution input.

This is NOT ground-truth validation — it measures whether the SR output
is consistent with the original observation.
"""

import numpy as np
import cv2
from app.validation.metrics import calculate_psnr, calculate_ssim


def calculate_observation_consistency(sr_output: np.ndarray,
                                      original_lr: np.ndarray,
                                      scale_factor: int) -> dict:
    """Calculate observation consistency between SR output and original LR input.
    
    Process:
    1. Downsample SR output by scale_factor using area interpolation
    2. Compare downsampled SR with original LR
    3. Compute PSNR and SSIM between them
    
    This validates that the SR reconstruction is consistent with
    the original observation, NOT that generated details are ground truth.
    
    Args:
        sr_output: Super-resolved output (H*s, W*s, C) or (H*s, W*s)
        original_lr: Original low-resolution input (H, W, C) or (H, W)
        scale_factor: The scale factor used in SR
    
    Returns:
        Dict with consistency metrics and interpretation
    """
    # Determine target dimensions from original LR
    if original_lr.ndim == 3:
        target_h, target_w = original_lr.shape[:2]
    else:
        target_h, target_w = original_lr.shape
    
    # Downsample SR output using area interpolation (anti-aliased)
    if sr_output.ndim == 3:
        downsampled = cv2.resize(sr_output, (target_w, target_h),
                                  interpolation=cv2.INTER_AREA)
    else:
        downsampled = cv2.resize(sr_output, (target_w, target_h),
                                  interpolation=cv2.INTER_AREA)
    
    # Ensure same value range
    if original_lr.max() > 1.0 and downsampled.max() <= 1.0:
        original_lr_norm = original_lr / original_lr.max()
    elif downsampled.max() > 1.0 and original_lr.max() <= 1.0:
        downsampled = downsampled / max(downsampled.max(), 1e-10)
        original_lr_norm = original_lr
    else:
        original_lr_norm = original_lr
    
    # Ensure shapes match
    if downsampled.shape != original_lr_norm.shape:
        # Resize to match
        if original_lr_norm.ndim == 3:
            h, w = original_lr_norm.shape[:2]
        else:
            h, w = original_lr_norm.shape
        downsampled = cv2.resize(downsampled, (w, h), interpolation=cv2.INTER_AREA)
    
    # Calculate consistency metrics
    consistency_psnr = calculate_psnr(downsampled, original_lr_norm)
    consistency_ssim = calculate_ssim(downsampled, original_lr_norm)
    
    # Determine quality interpretation
    if consistency_psnr > 35:
        psnr_quality = 'excellent'
    elif consistency_psnr > 30:
        psnr_quality = 'good'
    elif consistency_psnr > 25:
        psnr_quality = 'moderate'
    else:
        psnr_quality = 'low'
    
    return {
        'consistency_psnr': float(consistency_psnr),
        'consistency_ssim': float(consistency_ssim),
        'psnr_quality': psnr_quality,
        'method_description': (
            f'The SR output ({sr_output.shape[1]}×{sr_output.shape[0]}) was downsampled '
            f'back to the original resolution ({target_w}×{target_h}) using area '
            f'interpolation, then compared with the original LR input.'
        ),
        'interpretation': (
            'Observation consistency measures whether the SR reconstruction preserves '
            'the original low-resolution information. High consistency (high PSNR/SSIM) '
            'means the generated output is compatible with the original observation. '
            'This does NOT prove that generated high-resolution details are ground truth.'
        ),
    }
