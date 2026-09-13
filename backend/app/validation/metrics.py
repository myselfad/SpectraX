"""Reference-based validation metrics for image quality assessment.

These metrics are ONLY calculated when a valid reference (ground-truth)
image is available. Do not fabricate values.
"""

import numpy as np


def calculate_psnr(prediction: np.ndarray, reference: np.ndarray) -> float:
    """Peak Signal-to-Noise Ratio.
    
    Higher is better. Measures pixel-level fidelity.
    
    Args:
        prediction: Predicted image (H, W) or (H, W, C), values in [0, 1]
        reference: Reference image, same shape as prediction
    
    Returns:
        PSNR value in dB
    """
    mse = np.mean((prediction.astype(np.float64) - reference.astype(np.float64)) ** 2)
    if mse < 1e-10:
        return float('inf')
    max_pixel = 1.0
    psnr = 10 * np.log10(max_pixel ** 2 / mse)
    return float(psnr)


def calculate_ssim(prediction: np.ndarray, reference: np.ndarray) -> float:
    """Structural Similarity Index Measure.
    
    Higher is better (max 1.0). Measures structural similarity.
    
    Args:
        prediction: Predicted image, values in [0, 1]
        reference: Reference image, same shape
    
    Returns:
        SSIM value in [0, 1]
    """
    try:
        from skimage.metrics import structural_similarity
        
        if prediction.ndim == 3:
            return float(structural_similarity(prediction, reference, 
                                               channel_axis=2, data_range=1.0))
        else:
            return float(structural_similarity(prediction, reference, data_range=1.0))
    except ImportError:
        # Manual SSIM implementation
        return _manual_ssim(prediction, reference)


def _manual_ssim(pred: np.ndarray, ref: np.ndarray) -> float:
    """Simple SSIM implementation without scikit-image."""
    C1 = (0.01 * 1.0) ** 2
    C2 = (0.03 * 1.0) ** 2
    
    if pred.ndim == 3:
        ssim_vals = []
        for c in range(pred.shape[2]):
            ssim_vals.append(_manual_ssim(pred[:, :, c], ref[:, :, c]))
        return float(np.mean(ssim_vals))
    
    mu_x = np.mean(pred)
    mu_y = np.mean(ref)
    sigma_x2 = np.var(pred)
    sigma_y2 = np.var(ref)
    sigma_xy = np.mean((pred - mu_x) * (ref - mu_y))
    
    numerator = (2 * mu_x * mu_y + C1) * (2 * sigma_xy + C2)
    denominator = (mu_x**2 + mu_y**2 + C1) * (sigma_x2 + sigma_y2 + C2)
    
    return float(numerator / denominator)


def calculate_sam(prediction: np.ndarray, reference: np.ndarray) -> float:
    """Spectral Angle Mapper for multispectral data.
    
    Lower is better. Measures spectral fidelity.
    
    Args:
        prediction: Predicted image (H, W, C)
        reference: Reference image (H, W, C)
    
    Returns:
        Mean SAM value in degrees
    """
    if prediction.ndim != 3 or reference.ndim != 3:
        return 0.0
    
    # Reshape to (N, C) where N = H*W
    pred_flat = prediction.reshape(-1, prediction.shape[2]).astype(np.float64)
    ref_flat = reference.reshape(-1, reference.shape[2]).astype(np.float64)
    
    # Compute spectral angle
    dot_product = np.sum(pred_flat * ref_flat, axis=1)
    norm_pred = np.linalg.norm(pred_flat, axis=1)
    norm_ref = np.linalg.norm(ref_flat, axis=1)
    
    # Avoid division by zero
    denominator = norm_pred * norm_ref
    mask = denominator > 1e-10
    
    cos_angle = np.zeros_like(dot_product)
    cos_angle[mask] = dot_product[mask] / denominator[mask]
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    
    angles = np.arccos(cos_angle)
    mean_angle = np.mean(angles)
    
    return float(np.degrees(mean_angle))


def calculate_ergas(prediction: np.ndarray, reference: np.ndarray, scale: int) -> float:
    """Erreur Relative Globale Adimensionnelle de Synthese.
    
    Lower is better. Measures overall spectral quality relative to scale.
    
    Args:
        prediction: Predicted image (H, W, C)
        reference: Reference image (H, W, C)
        scale: Scale factor
    
    Returns:
        ERGAS value
    """
    if prediction.ndim != 3 or reference.ndim != 3:
        return 0.0
    
    num_bands = prediction.shape[2]
    sum_term = 0.0
    
    for b in range(num_bands):
        pred_band = prediction[:, :, b].astype(np.float64)
        ref_band = reference[:, :, b].astype(np.float64)
        
        rmse = np.sqrt(np.mean((pred_band - ref_band) ** 2))
        mean_ref = np.mean(ref_band)
        
        if abs(mean_ref) > 1e-10:
            sum_term += (rmse / mean_ref) ** 2
    
    ergas = 100.0 / scale * np.sqrt(sum_term / num_bands)
    return float(ergas)


def calculate_metrics(prediction: np.ndarray, reference: np.ndarray = None,
                      scale: int = 4) -> dict:
    """Calculate all applicable metrics.
    
    Reference-based metrics are ONLY calculated when a valid reference exists.
    
    Args:
        prediction: SR output
        reference: Ground-truth reference (or None)
        scale: Scale factor
    
    Returns:
        Dict with calculated metrics and metadata
    """
    result = {
        'reference_available': reference is not None,
        'reference_metrics': None,
    }
    
    if reference is not None:
        # Verify shapes match
        if prediction.shape != reference.shape:
            result['reference_metrics'] = {
                'error': f'Shape mismatch: prediction {prediction.shape} vs reference {reference.shape}',
                'calculated': False,
            }
        else:
            result['reference_metrics'] = {
                'psnr': calculate_psnr(prediction, reference),
                'ssim': calculate_ssim(prediction, reference),
                'sam': calculate_sam(prediction, reference) if prediction.ndim == 3 else None,
                'ergas': calculate_ergas(prediction, reference, scale) if prediction.ndim == 3 else None,
                'calculated': True,
                'interpretation': {
                    'psnr': 'Higher is better (dB). Measures pixel-level fidelity.',
                    'ssim': 'Higher is better (0-1). Measures structural similarity.',
                    'sam': 'Lower is better (degrees). Measures spectral fidelity.',
                    'ergas': 'Lower is better. Measures overall spectral quality.',
                },
            }
    
    return result
