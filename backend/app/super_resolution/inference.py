"""Super-resolution inference engine.

Performs tile-based inference using the loaded SwinIR model.
Handles tensor conversion, device management, and patch stitching.
"""

import numpy as np
import torch
from app.super_resolution.model import ModelManager
from app.preprocessing.tiling import create_tiles, reconstruct_from_tiles


def run_sr_inference(model_manager: ModelManager, image_rgb: np.ndarray,
                     tile_size: int = 48, overlap: int = 8) -> np.ndarray:
    """Run super-resolution inference on an RGB image.
    
    Uses tile-based processing for memory efficiency. For small images,
    processes in a single pass. For larger images, splits into overlapping
    tiles, processes each, and stitches with blending.
    
    Args:
        model_manager: ModelManager instance with loaded model
        image_rgb: RGB image array (H, W, 3) normalized to [0, 1]
        tile_size: Tile size for patch-based inference
        overlap: Overlap between adjacent tiles
    
    Returns:
        SR output array (H*scale, W*scale, 3) in [0, 1]
    """
    model = model_manager.model
    device = model_manager.device
    scale = 4  # SwinIR-M x4
    
    H, W, C = image_rgb.shape
    
    # Decide: single-pass or tiled
    if H <= tile_size and W <= tile_size:
        return _inference_single(model, device, image_rgb, scale)
    else:
        return _inference_tiled(model, device, image_rgb, tile_size, overlap, scale)


def _inference_single(model: torch.nn.Module, device: torch.device,
                      image: np.ndarray, scale: int) -> np.ndarray:
    """Process entire image in a single forward pass."""
    H, W, C = image.shape
    
    # HWC -> CHW -> BCHW tensor
    tensor = torch.from_numpy(image.transpose(2, 0, 1)).float().unsqueeze(0).to(device)
    
    with torch.no_grad():
        output = model(tensor)
    
    # BCHW -> CHW -> HWC
    result = output.squeeze(0).cpu().numpy().transpose(1, 2, 0)
    result = np.clip(result, 0.0, 1.0)
    
    return result[:H*scale, :W*scale, :]


def _inference_tiled(model: torch.nn.Module, device: torch.device,
                     image: np.ndarray, tile_size: int, overlap: int,
                     scale: int) -> np.ndarray:
    """Process image using overlapping tiles."""
    H, W, C = image.shape
    
    # Create tiles
    tiles = create_tiles(image, tile_size=tile_size, overlap=overlap)
    
    # Process each tile
    processed_tiles = []
    for tile_info in tiles:
        tile_data = tile_info['data']  # (tile_size, tile_size, C)
        
        # HWC -> CHW -> BCHW
        tensor = torch.from_numpy(tile_data.transpose(2, 0, 1)).float().unsqueeze(0).to(device)
        
        with torch.no_grad():
            output = model(tensor)
        
        # BCHW -> HWC
        processed = output.squeeze(0).cpu().numpy().transpose(1, 2, 0)
        processed = np.clip(processed, 0.0, 1.0)
        
        processed_tiles.append({
            'data': processed,
            'row': tile_info['row'],
            'col': tile_info['col'],
            'h': tile_info['h'],
            'w': tile_info['w'],
            'padded': tile_info.get('padded', False),
        })
    
    # Reconstruct from tiles
    output_h = H * scale
    output_w = W * scale
    result = reconstruct_from_tiles(
        processed_tiles,
        output_h=output_h,
        output_w=output_w,
        channels=C,
        tile_size=tile_size,
        overlap=overlap,
        scale=scale,
    )
    
    return np.clip(result, 0.0, 1.0)


def run_sr_inference_stochastic(model: torch.nn.Module, device: torch.device,
                                 image_rgb: np.ndarray, scale: int = 4) -> np.ndarray:
    """Run a single stochastic forward pass (model.train() mode).
    
    Used by MC-Dropout for uncertainty estimation.
    """
    H, W, C = image_rgb.shape
    tensor = torch.from_numpy(image_rgb.transpose(2, 0, 1)).float().unsqueeze(0).to(device)
    
    with torch.no_grad():
        output = model(tensor)
    
    result = output.squeeze(0).cpu().numpy().transpose(1, 2, 0)
    result = np.clip(result, 0.0, 1.0)
    
    return result[:H*scale, :W*scale, :]
