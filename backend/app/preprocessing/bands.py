"""Band detection and selection for multispectral satellite imagery.

Handles different band configurations:
- 4+ bands: Blue, Green, Red, NIR (Sentinel-2 convention)
- 3 bands: RGB
- 1 band: Grayscale
"""

import numpy as np


def detect_bands(data: np.ndarray, metadata: dict) -> dict:
    """Detect available bands from image data and metadata.
    
    Args:
        data: Image data in CHW format (C, H, W)
        metadata: Metadata dict with band_names, num_bands
    
    Returns:
        Dict with band configuration information
    """
    if data.ndim == 2:
        num_bands = 1
    elif data.ndim == 3:
        num_bands = data.shape[0]
    else:
        num_bands = 0
    
    band_names = metadata.get('band_names', [])
    if not band_names or len(band_names) != num_bands:
        band_names = _infer_band_names(num_bands)
    
    return {
        'num_bands': num_bands,
        'band_names': band_names,
        'has_rgb': num_bands >= 3,
        'has_nir': num_bands >= 4 and 'nir' in band_names,
        'shape': data.shape,
    }


def select_bands(data: np.ndarray, band_config: dict, 
                 selected: list[str]) -> dict[str, np.ndarray]:
    """Select and extract specified bands from image data.
    
    Args:
        data: Image data in CHW format (C, H, W)
        band_config: Band configuration from detect_bands
        selected: List of band names to select ['red', 'green', 'blue', 'nir']
    
    Returns:
        Dict mapping band name to 2D array (H, W)
    """
    band_names = band_config.get('band_names', [])
    num_bands = band_config.get('num_bands', 0)
    
    # Handle 2D input (single band)
    if data.ndim == 2:
        return {'gray': data.astype(np.float32)}
    
    result = {}
    
    for band_name in selected:
        band_name_lower = band_name.lower()
        
        if band_name_lower in band_names:
            idx = band_names.index(band_name_lower)
            if idx < num_bands:
                result[band_name_lower] = data[idx].astype(np.float32)
        elif band_name_lower == 'red' and num_bands >= 3:
            # Standard RGB: R=0 for 3-band, R=2 for 4+ band (B,G,R,NIR)
            idx = 2 if num_bands >= 4 else 0
            result['red'] = data[idx].astype(np.float32)
        elif band_name_lower == 'green' and num_bands >= 3:
            result['green'] = data[1].astype(np.float32)
        elif band_name_lower == 'blue' and num_bands >= 3:
            idx = 0 if num_bands >= 4 else 2
            result['blue'] = data[idx].astype(np.float32)
        elif band_name_lower == 'nir' and num_bands >= 4:
            result['nir'] = data[3].astype(np.float32)
    
    # Fallback: if no bands matched, use available data as RGB
    if not result:
        if num_bands >= 3:
            result = {
                'red': data[0].astype(np.float32),
                'green': data[1].astype(np.float32),
                'blue': data[2].astype(np.float32),
            }
            if num_bands >= 4:
                result['nir'] = data[3].astype(np.float32)
        elif num_bands == 1:
            result = {'gray': data[0].astype(np.float32)}
        else:
            for i in range(num_bands):
                result[f'band_{i+1}'] = data[i].astype(np.float32)
    
    return result


def _infer_band_names(num_bands: int) -> list[str]:
    """Infer band names from band count."""
    if num_bands >= 4:
        base = ['blue', 'green', 'red', 'nir']
        if num_bands > 4:
            base += [f'band_{i+1}' for i in range(4, num_bands)]
        return base
    elif num_bands == 3:
        return ['red', 'green', 'blue']
    elif num_bands == 1:
        return ['gray']
    else:
        return [f'band_{i+1}' for i in range(num_bands)]
