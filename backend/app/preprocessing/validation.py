"""File validation for satellite imagery uploads.

Validates file format, integrity, size, and basic readability.
"""

import os
from app.core.config import settings


def validate_file(filepath: str) -> dict:
    """Validate an uploaded file for processing compatibility.
    
    Checks:
    - File exists
    - Extension is supported
    - File size is within limits
    - File can be opened/read
    - Basic data integrity
    
    Args:
        filepath: Path to the uploaded file
    
    Returns:
        Dict with is_valid, errors, warnings, file_type
    """
    errors = []
    warnings = []
    file_type = 'unknown'
    
    # Check existence
    if not os.path.exists(filepath):
        return {'is_valid': False, 'errors': ['File does not exist'], 
                'warnings': [], 'file_type': 'unknown'}
    
    # Check extension
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        errors.append(f'Unsupported file format: {ext}. Supported: {", ".join(settings.ALLOWED_EXTENSIONS)}')
        return {'is_valid': False, 'errors': errors, 'warnings': warnings, 'file_type': 'unknown'}
    
    # Check file size
    file_size = os.path.getsize(filepath)
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        errors.append(f'File size ({file_size / 1024 / 1024:.1f} MB) exceeds maximum ({settings.MAX_FILE_SIZE_MB} MB)')
    if file_size == 0:
        errors.append('File is empty')
    
    # Determine file type and validate readability
    if ext in ('.tif', '.tiff'):
        file_type = 'geotiff'
        _validate_geotiff(filepath, errors, warnings)
    else:
        file_type = 'standard_image'
        _validate_standard_image(filepath, errors, warnings)
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'file_type': file_type,
    }


def _validate_geotiff(filepath: str, errors: list, warnings: list):
    """Validate GeoTIFF-specific properties."""
    try:
        import rasterio
        with rasterio.open(filepath) as src:
            if src.count == 0:
                errors.append('GeoTIFF has no bands')
            if src.width == 0 or src.height == 0:
                errors.append('GeoTIFF has zero dimensions')
            if src.width > 10000 or src.height > 10000:
                warnings.append(f'Large image ({src.width}×{src.height}). Processing may be slow.')
            if not src.crs:
                warnings.append('No CRS defined in GeoTIFF')
            
            # Check for corrupted data
            try:
                _ = src.read(1, window=rasterio.windows.Window(0, 0, min(10, src.width), min(10, src.height)))
            except Exception:
                errors.append('GeoTIFF data appears corrupted (cannot read sample)')
                
    except ImportError:
        warnings.append('Rasterio not available. Limited GeoTIFF validation.')
        try:
            from PIL import Image
            img = Image.open(filepath)
            img.verify()
        except Exception as e:
            errors.append(f'Cannot open file: {str(e)}')
    except Exception as e:
        errors.append(f'Invalid GeoTIFF: {str(e)}')


def _validate_standard_image(filepath: str, errors: list, warnings: list):
    """Validate standard image format (PNG, JPG)."""
    try:
        from PIL import Image
        img = Image.open(filepath)
        img.verify()
        
        # Reopen to get properties (verify closes the file)
        img = Image.open(filepath)
        w, h = img.size
        
        if w == 0 or h == 0:
            errors.append('Image has zero dimensions')
        if w > 10000 or h > 10000:
            warnings.append(f'Large image ({w}×{h}). Processing may be slow.')
        if img.mode not in ('L', 'RGB', 'RGBA', 'I', 'F'):
            warnings.append(f'Unusual image mode: {img.mode}')
            
    except Exception as e:
        errors.append(f'Cannot open image: {str(e)}')
