"""Metadata extraction from satellite imagery and standard image files."""

import os


def extract_metadata(filepath: str) -> dict:
    """Extract metadata from an image file.
    
    For GeoTIFF: extracts CRS, transform, bands, resolution, NoData.
    For standard images: extracts dimensions, bands, basic info.
    
    Args:
        filepath: Path to the image file
    
    Returns:
        Dict with image metadata
    """
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext in ('.tif', '.tiff'):
        return _extract_geotiff_metadata(filepath)
    else:
        return _extract_standard_metadata(filepath)


def _extract_geotiff_metadata(filepath: str) -> dict:
    """Extract metadata from GeoTIFF using rasterio."""
    try:
        import rasterio
        with rasterio.open(filepath) as src:
            metadata = {
                'width': src.width,
                'height': src.height,
                'num_bands': src.count,
                'crs': str(src.crs) if src.crs else None,
                'transform': list(src.transform) if src.transform else None,
                'nodata': src.nodata,
                'dtype': str(src.dtypes[0]),
                'driver': src.driver,
            }
            
            # Spatial resolution
            if src.transform:
                metadata['spatial_resolution'] = {
                    'x': round(abs(src.transform[0]), 4),
                    'y': round(abs(src.transform[4]), 4),
                    'unit': 'meters' if src.crs and src.crs.is_projected else 'degrees'
                }
            else:
                metadata['spatial_resolution'] = None
            
            # Band names heuristic
            descriptions = src.descriptions
            if descriptions and any(d is not None for d in descriptions):
                metadata['band_names'] = [d if d else f'band_{i+1}' for i, d in enumerate(descriptions)]
            else:
                metadata['band_names'] = _infer_band_names(src.count)
            
            # Bounds
            if src.bounds:
                metadata['bounds'] = {
                    'left': src.bounds.left,
                    'bottom': src.bounds.bottom,
                    'right': src.bounds.right,
                    'top': src.bounds.top,
                }
            
        return metadata
        
    except ImportError:
        return _extract_standard_metadata(filepath)
    except Exception as e:
        return {
            'width': 0, 'height': 0, 'num_bands': 0,
            'band_names': [], 'crs': None, 'transform': None,
            'spatial_resolution': None, 'nodata': None,
            'dtype': 'unknown', 'driver': 'unknown',
            'error': str(e),
        }


def _extract_standard_metadata(filepath: str) -> dict:
    """Extract metadata from standard image (PNG, JPG)."""
    try:
        from PIL import Image
        img = Image.open(filepath)
        w, h = img.size
        
        # Determine band count
        mode_to_bands = {
            'L': 1, 'LA': 2, 'RGB': 3, 'RGBA': 4,
            'I': 1, 'F': 1, 'P': 1,
        }
        num_bands = mode_to_bands.get(img.mode, 3)
        
        return {
            'width': w,
            'height': h,
            'num_bands': num_bands,
            'band_names': _infer_band_names(num_bands),
            'crs': None,
            'transform': None,
            'spatial_resolution': None,
            'nodata': None,
            'dtype': 'uint8',
            'driver': img.format or 'PIL',
        }
    except Exception as e:
        return {
            'width': 0, 'height': 0, 'num_bands': 0,
            'band_names': [], 'crs': None, 'transform': None,
            'spatial_resolution': None, 'nodata': None,
            'dtype': 'unknown', 'driver': 'unknown',
            'error': str(e),
        }


def _infer_band_names(num_bands: int) -> list[str]:
    """Infer band names from band count using common satellite conventions."""
    if num_bands >= 4:
        # Assume Sentinel-2 style: Blue, Green, Red, NIR
        base = ['blue', 'green', 'red', 'nir']
        if num_bands > 4:
            base += [f'band_{i+1}' for i in range(4, num_bands)]
        return base
    elif num_bands == 3:
        return ['red', 'green', 'blue']
    elif num_bands == 1:
        return ['gray']
    elif num_bands == 2:
        return ['band_1', 'band_2']
    else:
        return [f'band_{i+1}' for i in range(num_bands)]
