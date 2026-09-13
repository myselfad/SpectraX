"""File I/O utilities for reading/writing satellite imagery and standard images."""

import os
import numpy as np
from PIL import Image

def read_image(filepath: str) -> tuple[np.ndarray, dict]:
    """Read image file (GeoTIFF or standard format).
    
    Returns:
        Tuple of (data as CHW float32 array, metadata dict)
    """
    ext = os.path.splitext(filepath)[1].lower()
    metadata = {
        'filepath': filepath,
        'filename': os.path.basename(filepath),
        'file_size': os.path.getsize(filepath),
    }
    
    if ext in ('.tif', '.tiff'):
        return _read_geotiff(filepath, metadata)
    else:
        return _read_standard_image(filepath, metadata)


def _read_geotiff(filepath: str, metadata: dict) -> tuple[np.ndarray, dict]:
    """Read GeoTIFF with rasterio."""
    try:
        import rasterio
        with rasterio.open(filepath) as src:
            data = src.read().astype(np.float32)  # (C, H, W)
            
            metadata.update({
                'file_type': 'geotiff',
                'driver': src.driver,
                'width': src.width,
                'height': src.height,
                'num_bands': src.count,
                'crs': str(src.crs) if src.crs else None,
                'transform': list(src.transform) if src.transform else None,
                'nodata': src.nodata,
                'dtype': str(src.dtypes[0]),
                'bounds': dict(zip(['left','bottom','right','top'], src.bounds)) if src.bounds else None,
            })
            
            # Estimate spatial resolution from transform
            if src.transform:
                metadata['spatial_resolution'] = {
                    'x': abs(src.transform[0]),
                    'y': abs(src.transform[4]),
                    'unit': 'meters' if src.crs and src.crs.is_projected else 'degrees'
                }
            
            # Band descriptions
            descriptions = src.descriptions
            if descriptions and any(d is not None for d in descriptions):
                metadata['band_descriptions'] = list(descriptions)
            
        return data, metadata
    except ImportError:
        # Fallback: try reading as standard image
        return _read_standard_image(filepath, metadata)


def _read_standard_image(filepath: str, metadata: dict) -> tuple[np.ndarray, dict]:
    """Read standard image (PNG, JPG) with PIL."""
    img = Image.open(filepath)
    data = np.array(img).astype(np.float32)
    
    if data.ndim == 2:
        # Grayscale -> (1, H, W)
        data = data[np.newaxis, :, :]
    elif data.ndim == 3:
        # (H, W, C) -> (C, H, W)
        if data.shape[2] == 4:
            # RGBA -> drop alpha
            data = data[:, :, :3]
        data = np.transpose(data, (2, 0, 1))
    
    metadata.update({
        'file_type': 'standard_image',
        'driver': img.format or 'PIL',
        'width': img.width,
        'height': img.height,
        'num_bands': data.shape[0],
        'crs': None,
        'transform': None,
        'nodata': None,
        'dtype': str(data.dtype),
        'spatial_resolution': None,
    })
    
    return data, metadata


def save_image(data: np.ndarray, filepath: str, metadata: dict | None = None):
    """Save image data to file.
    
    Args:
        data: Image data (CHW or HWC format)
        filepath: Output file path
        metadata: Optional geospatial metadata for GeoTIFF output
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext in ('.tif', '.tiff') and metadata and metadata.get('crs'):
        _save_geotiff(data, filepath, metadata)
    else:
        _save_standard_image(data, filepath)


def _save_geotiff(data: np.ndarray, filepath: str, metadata: dict):
    """Save as GeoTIFF with metadata."""
    import rasterio
    from rasterio.transform import Affine
    
    # Ensure CHW format
    if data.ndim == 2:
        data = data[np.newaxis, :, :]
    elif data.ndim == 3 and data.shape[2] in (1, 3, 4):
        data = np.transpose(data, (2, 0, 1))
    
    c, h, w = data.shape
    
    # Build transform
    transform = None
    if metadata.get('transform'):
        t = metadata['transform']
        if isinstance(t, (list, tuple)) and len(t) >= 6:
            transform = Affine(t[0], t[1], t[2], t[3], t[4], t[5])
    
    # Determine dtype for output
    if data.max() <= 1.0:
        out_data = (data * 65535).astype(np.uint16)
        dtype = rasterio.uint16
    else:
        out_data = data.astype(np.float32)
        dtype = rasterio.float32
    
    profile = {
        'driver': 'GTiff',
        'dtype': dtype,
        'width': w,
        'height': h,
        'count': c,
        'crs': metadata.get('crs'),
        'transform': transform,
        'compress': 'lzw',
    }
    
    with rasterio.open(filepath, 'w', **profile) as dst:
        dst.write(out_data)


def _save_standard_image(data: np.ndarray, filepath: str):
    """Save as standard image (PNG)."""
    # Ensure HWC for PIL
    if data.ndim == 2:
        arr = data
    elif data.ndim == 3:
        if data.shape[0] in (1, 3, 4):
            arr = np.transpose(data, (1, 2, 0))
        else:
            arr = data
        if arr.shape[2] == 1:
            arr = arr.squeeze(2)
    else:
        arr = data
    
    # Scale to uint8
    if arr.max() <= 1.0 and arr.min() >= 0.0:
        arr = (arr * 255).clip(0, 255).astype(np.uint8)
    elif arr.max() > 255:
        arr = ((arr / arr.max()) * 255).clip(0, 255).astype(np.uint8)
    else:
        arr = arr.clip(0, 255).astype(np.uint8)
    
    Image.fromarray(arr).save(filepath)


def get_file_info(filepath: str) -> dict:
    """Get basic file information."""
    stat = os.stat(filepath)
    return {
        'size': stat.st_size,
        'extension': os.path.splitext(filepath)[1].lower(),
        'exists': True,
        'filename': os.path.basename(filepath),
    }
