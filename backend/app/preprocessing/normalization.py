"""Band normalization for satellite imagery preprocessing.

Supports percentile-based and min-max normalization. Preserves normalization
parameters for invertible denormalization.
"""

import numpy as np


def normalize_band(band: np.ndarray, method: str = 'percentile',
                   percentile_low: float = 2, percentile_high: float = 98) -> tuple[np.ndarray, dict]:
    """Normalize a single band to [0, 1].
    
    Args:
        band: 2D array (H, W)
        method: 'percentile' or 'minmax'
        percentile_low: Lower percentile for clipping (percentile method)
        percentile_high: Upper percentile for clipping (percentile method)
    
    Returns:
        Tuple of (normalized band, normalization parameters for reversal)
    """
    # Handle NoData / invalid values
    valid_mask = np.isfinite(band)
    if not valid_mask.any():
        return np.zeros_like(band), {'method': method, 'low': 0, 'high': 1, 'valid': False}
    
    valid_data = band[valid_mask]
    
    if method == 'percentile':
        low = float(np.percentile(valid_data, percentile_low))
        high = float(np.percentile(valid_data, percentile_high))
    else:  # minmax
        low = float(valid_data.min())
        high = float(valid_data.max())
    
    # Avoid division by zero
    if high - low < 1e-10:
        high = low + 1.0
    
    normalized = (band - low) / (high - low)
    normalized = np.clip(normalized, 0.0, 1.0)
    
    params = {
        'method': method,
        'low': low,
        'high': high,
        'valid': True,
        'percentile_low': percentile_low,
        'percentile_high': percentile_high,
    }
    
    return normalized.astype(np.float32), params


def denormalize_band(band: np.ndarray, params: dict) -> np.ndarray:
    """Reverse normalization using stored parameters.
    
    Args:
        band: Normalized band (H, W) in [0, 1]
        params: Normalization parameters from normalize_band
    
    Returns:
        Denormalized band
    """
    if not params.get('valid', True):
        return band
    
    low = params['low']
    high = params['high']
    return (band * (high - low) + low).astype(np.float32)


def normalize_for_model(bands: dict[str, np.ndarray]) -> tuple[np.ndarray, dict]:
    """Normalize all bands and prepare model-ready array.
    
    Normalizes each band independently using percentile normalization,
    then stacks RGB bands for model input. NIR is normalized separately.
    
    Args:
        bands: Dict mapping band name to 2D array {'red': (H,W), 'green': (H,W), ...}
    
    Returns:
        Tuple of:
        - rgb_array: (H, W, 3) float32 array in [0, 1] (RGB order for model)
        - norm_info: Dict with normalization params and separated NIR data
    """
    norm_params = {}
    normalized_bands = {}
    
    for name, band_data in bands.items():
        norm_band, params = normalize_band(band_data, method='percentile')
        normalized_bands[name] = norm_band
        norm_params[name] = params
    
    # Build RGB array for model input (H, W, 3)
    rgb_names = ['red', 'green', 'blue']
    available_rgb = [n for n in rgb_names if n in normalized_bands]
    
    if len(available_rgb) == 3:
        rgb_array = np.stack([normalized_bands['red'], normalized_bands['green'], 
                              normalized_bands['blue']], axis=-1)
    elif len(normalized_bands) >= 3:
        # Use first 3 bands as RGB
        band_keys = list(normalized_bands.keys())
        rgb_array = np.stack([normalized_bands[band_keys[0]], 
                              normalized_bands[band_keys[1]],
                              normalized_bands[band_keys[2]]], axis=-1)
    elif len(normalized_bands) == 1:
        # Grayscale -> replicate
        single_band = list(normalized_bands.values())[0]
        rgb_array = np.stack([single_band, single_band, single_band], axis=-1)
    else:
        # 2 bands -> pad with zeros
        band_keys = list(normalized_bands.keys())
        arrays = [normalized_bands[k] for k in band_keys]
        while len(arrays) < 3:
            arrays.append(np.zeros_like(arrays[0]))
        rgb_array = np.stack(arrays[:3], axis=-1)
    
    norm_info = {
        'params': norm_params,
        'band_order': list(bands.keys()),
        'rgb_bands': available_rgb,
        'nir_data': normalized_bands.get('nir'),
        'has_nir': 'nir' in normalized_bands,
    }
    
    return rgb_array.astype(np.float32), norm_info
