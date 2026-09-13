"""Post-processing for super-resolution output.

Handles NIR upsampling, output clipping, and GeoTIFF generation.
"""

import os
import numpy as np
import cv2


def postprocess_sr_output(sr_rgb: np.ndarray, nir_band: np.ndarray | None,
                          scale_factor: int) -> dict:
    """Post-process super-resolution output.
    
    Clips RGB output, upscales NIR via bicubic interpolation,
    and ensures spatial alignment between all bands.
    
    Args:
        sr_rgb: SR RGB output (H*s, W*s, 3) in [0, 1]
        nir_band: Original NIR band (H, W) in [0, 1], or None
        scale_factor: Upscale factor
    
    Returns:
        Dict with:
        - 'rgb': clipped SR RGB (H*s, W*s, 3)
        - 'nir': upscaled NIR (H*s, W*s) or None
        - 'band_methods': dict mapping band name to processing method
    """
    # Clip RGB to valid range
    rgb_out = np.clip(sr_rgb, 0.0, 1.0).astype(np.float32)
    target_h, target_w = rgb_out.shape[:2]
    
    band_methods = {
        'red': {'method': 'swinir_sr', 'description': 'SwinIR transformer super-resolution'},
        'green': {'method': 'swinir_sr', 'description': 'SwinIR transformer super-resolution'},
        'blue': {'method': 'swinir_sr', 'description': 'SwinIR transformer super-resolution'},
    }
    
    nir_out = None
    if nir_band is not None:
        # Upscale NIR using bicubic interpolation
        nir_out = cv2.resize(nir_band, (target_w, target_h),
                             interpolation=cv2.INTER_CUBIC)
        nir_out = np.clip(nir_out, 0.0, 1.0).astype(np.float32)
        band_methods['nir'] = {
            'method': 'bicubic_interpolation',
            'description': 'Bicubic interpolation baseline (not AI super-resolved)'
        }
    
    return {
        'rgb': rgb_out,
        'nir': nir_out,
        'band_methods': band_methods,
    }


def create_output_geotiff(sr_data: dict, original_metadata: dict, output_path: str):
    """Create output GeoTIFF preserving geospatial metadata.
    
    Updates the transform to reflect the higher resolution output.
    
    Args:
        sr_data: Dict from postprocess_sr_output
        original_metadata: Metadata from the original input
        output_path: Path to save the output GeoTIFF
    """
    try:
        import rasterio
        from rasterio.transform import Affine
    except ImportError:
        # Fallback: save as regular image
        from app.utils.io import _save_standard_image
        rgb = sr_data['rgb']
        if rgb.ndim == 3:
            _save_standard_image(np.transpose(rgb, (2, 0, 1)), output_path)
        return
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    rgb = sr_data['rgb']  # (H, W, 3)
    nir = sr_data.get('nir')  # (H, W) or None
    
    if nir is not None:
        # Stack all bands: B, G, R, NIR (CHW)
        all_bands = np.stack([
            rgb[:, :, 2],  # Blue
            rgb[:, :, 1],  # Green
            rgb[:, :, 0],  # Red
            nir             # NIR
        ], axis=0)
    else:
        all_bands = np.transpose(rgb, (2, 0, 1))  # (3, H, W)
    
    c, h, w = all_bands.shape
    
    # Update transform for higher resolution
    transform = None
    crs = original_metadata.get('crs')
    if original_metadata.get('transform'):
        t = original_metadata['transform']
        if isinstance(t, (list, tuple)) and len(t) >= 6:
            orig_transform = Affine(t[0], t[1], t[2], t[3], t[4], t[5])
            scale = original_metadata.get('_scale_factor', 4)
            # New pixel size = old pixel size / scale
            transform = Affine(
                orig_transform.a / scale, orig_transform.b, orig_transform.c,
                orig_transform.d, orig_transform.e / scale, orig_transform.f
            )
    
    # Convert to uint16 for GeoTIFF
    out_data = (all_bands * 65535).clip(0, 65535).astype(np.uint16)
    
    profile = {
        'driver': 'GTiff',
        'dtype': rasterio.uint16,
        'width': w,
        'height': h,
        'count': c,
        'compress': 'lzw',
    }
    if crs:
        profile['crs'] = crs
    if transform:
        profile['transform'] = transform
    
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(out_data)
        band_names = ['Blue', 'Green', 'Red', 'NIR'] if c == 4 else ['Red', 'Green', 'Blue']
        for i, name in enumerate(band_names):
            dst.set_band_description(i + 1, name)
