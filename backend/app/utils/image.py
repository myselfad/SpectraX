"""Image visualization utilities for generating preview images and comparison views."""

import os
import numpy as np
from PIL import Image
import io


def array_to_png_bytes(array: np.ndarray, normalize: bool = True) -> bytes:
    """Convert numpy array to PNG bytes.
    
    Args:
        array: Image data (HWC or CHW, float or uint8)
        normalize: Whether to normalize to [0, 255]
    
    Returns:
        PNG image as bytes
    """
    arr = _prepare_for_display(array)
    if normalize and arr.dtype != np.uint8:
        if arr.max() <= 1.0:
            arr = (arr * 255).clip(0, 255).astype(np.uint8)
        else:
            arr = arr.clip(0, 255).astype(np.uint8)
    
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def save_visualization(array: np.ndarray, filepath: str, title: str = None):
    """Save array as a visualization PNG."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    arr = _prepare_for_display(array)
    
    if arr.max() <= 1.0:
        arr = (arr * 255).clip(0, 255).astype(np.uint8)
    else:
        arr = arr.clip(0, 255).astype(np.uint8)
    
    img = Image.fromarray(arr)
    img.save(filepath)


def create_comparison_image(original: np.ndarray, sr_output: np.ndarray, output_path: str):
    """Create side-by-side comparison image.
    
    Upscales original to match SR output dimensions for visual comparison.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    orig = _prepare_for_display(original)
    sr = _prepare_for_display(sr_output)
    
    # Scale to uint8
    if orig.max() <= 1.0:
        orig = (orig * 255).clip(0, 255).astype(np.uint8)
    else:
        orig = orig.clip(0, 255).astype(np.uint8)
        
    if sr.max() <= 1.0:
        sr = (sr * 255).clip(0, 255).astype(np.uint8)
    else:
        sr = sr.clip(0, 255).astype(np.uint8)
    
    # Resize original to match SR output height for comparison
    orig_img = Image.fromarray(orig)
    sr_img = Image.fromarray(sr)
    
    target_h = sr_img.height
    target_w = sr_img.width
    orig_resized = orig_img.resize((target_w, target_h), Image.Resampling.NEAREST)
    
    # Create side-by-side with separator
    sep_width = 4
    total_w = target_w * 2 + sep_width
    comparison = Image.new('RGB', (total_w, target_h), color=(40, 40, 40))
    comparison.paste(orig_resized, (0, 0))
    comparison.paste(sr_img, (target_w + sep_width, 0))
    
    comparison.save(output_path)


def save_rgb_preview(data: np.ndarray, filepath: str):
    """Save RGB visualization from multi-band data.
    
    Args:
        data: CHW or HWC array with at least 3 bands
        filepath: Output PNG path
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    arr = _prepare_for_display(data)
    
    if arr.ndim == 3 and arr.shape[2] > 3:
        arr = arr[:, :, :3]
    
    if arr.max() <= 1.0:
        arr = (arr * 255).clip(0, 255).astype(np.uint8)
    else:
        arr = arr.clip(0, 255).astype(np.uint8)
    
    Image.fromarray(arr).save(filepath)


def save_band_preview(band: np.ndarray, filepath: str, band_name: str, colormap: str = 'gray'):
    """Save single-band visualization with colormap."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(1, 1, figsize=(8, 8))
        
        # Normalize band for display
        display_data = band.copy()
        if display_data.max() > display_data.min():
            display_data = (display_data - display_data.min()) / (display_data.max() - display_data.min())
        
        im = ax.imshow(display_data, cmap=colormap)
        ax.set_title(f'{band_name.upper()} Band', fontsize=14, fontweight='bold')
        ax.axis('off')
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        plt.tight_layout()
        plt.savefig(filepath, dpi=100, bbox_inches='tight', facecolor='#1a1a2e')
        plt.close(fig)
    except ImportError:
        # Fallback without matplotlib
        if band.max() <= 1.0:
            arr = (band * 255).clip(0, 255).astype(np.uint8)
        else:
            arr = band.clip(0, 255).astype(np.uint8)
        Image.fromarray(arr, mode='L').save(filepath)


def _prepare_for_display(array: np.ndarray) -> np.ndarray:
    """Prepare array for display by converting to HWC format.
    
    Handles both CHW and HWC formats, and both float and uint8 dtypes.
    """
    arr = array.copy()
    
    if arr.ndim == 2:
        # Grayscale -> RGB
        arr = np.stack([arr, arr, arr], axis=-1)
    elif arr.ndim == 3:
        # Check if CHW format (C is small and first dim)
        if arr.shape[0] in (1, 3, 4) and arr.shape[0] < arr.shape[1] and arr.shape[0] < arr.shape[2]:
            arr = np.transpose(arr, (1, 2, 0))
        
        # Handle single channel
        if arr.shape[2] == 1:
            arr = np.repeat(arr, 3, axis=2)
        elif arr.shape[2] == 4:
            arr = arr[:, :, :3]
        elif arr.shape[2] > 4:
            # Take first 3 bands as RGB (or R,G,B if 4+ band)
            arr = arr[:, :, :3]
    
    return arr.astype(np.float32)
