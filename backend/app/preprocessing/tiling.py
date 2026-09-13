"""Tile/patch generation and reconstruction for memory-efficient processing.

Splits large images into overlapping tiles for model inference,
then stitches results back with linear blending in overlap regions.
"""

import numpy as np


def create_tiles(image: np.ndarray, tile_size: int = 48, overlap: int = 8) -> list[dict]:
    """Split image into overlapping tiles for model inference.
    
    Args:
        image: Input image (H, W, C) or (H, W)
        tile_size: Size of each tile (square)
        overlap: Number of pixels to overlap between adjacent tiles
    
    Returns:
        List of tile dicts, each containing:
        - 'data': tile array (H, W, C) or (H, W)
        - 'row': starting row in original image
        - 'col': starting col in original image
        - 'h': actual height (before padding)
        - 'w': actual width (before padding)
        - 'padded': whether tile was padded
    """
    if image.ndim == 2:
        H, W = image.shape
        C = None
    else:
        H, W, C = image.shape
    
    stride = tile_size - overlap
    if stride <= 0:
        stride = tile_size // 2
    
    tiles = []
    
    row = 0
    while row < H:
        col = 0
        while col < W:
            # Determine tile bounds
            r_end = min(row + tile_size, H)
            c_end = min(col + tile_size, W)
            actual_h = r_end - row
            actual_w = c_end - col
            
            # Extract tile
            if C is not None:
                tile_data = image[row:r_end, col:c_end, :]
            else:
                tile_data = image[row:r_end, col:c_end]
            
            # Pad if needed (tile is smaller than tile_size)
            padded = False
            if actual_h < tile_size or actual_w < tile_size:
                if C is not None:
                    padded_tile = np.zeros((tile_size, tile_size, C), dtype=image.dtype)
                    padded_tile[:actual_h, :actual_w, :] = tile_data
                else:
                    padded_tile = np.zeros((tile_size, tile_size), dtype=image.dtype)
                    padded_tile[:actual_h, :actual_w] = tile_data
                tile_data = padded_tile
                padded = True
            
            tiles.append({
                'data': tile_data,
                'row': row,
                'col': col,
                'h': actual_h,
                'w': actual_w,
                'padded': padded,
            })
            
            col += stride
            if col >= W and c_end < W:
                col = W - tile_size
                if col < 0:
                    col = 0
                    break
            elif c_end >= W:
                break
        
        row += stride
        if row >= H and r_end < H:
            row = H - tile_size
            if row < 0:
                row = 0
                break
        elif r_end >= H:
            break
    
    return tiles


def reconstruct_from_tiles(tiles: list[dict], output_h: int, output_w: int,
                           channels: int, tile_size: int, overlap: int,
                           scale: int = 1) -> np.ndarray:
    """Reconstruct full image from overlapping tiles with linear blending.
    
    Args:
        tiles: List of tile dicts from create_tiles, each with 'data' (processed),
               'row', 'col', 'h', 'w' keys
        output_h: Height of the output image (original_h * scale)
        output_w: Width of the output image (original_w * scale)
        channels: Number of channels
        tile_size: Original tile size (before scaling)
        overlap: Original overlap (before scaling)
        scale: Scale factor applied by processing
    
    Returns:
        Reconstructed image (output_h, output_w, channels)
    """
    scaled_tile = tile_size * scale
    scaled_overlap = overlap * scale
    
    if channels > 0:
        output = np.zeros((output_h, output_w, channels), dtype=np.float32)
    else:
        output = np.zeros((output_h, output_w), dtype=np.float32)
    weight_map = np.zeros((output_h, output_w), dtype=np.float32)
    
    for tile_info in tiles:
        tile_data = tile_info['data']
        r = tile_info['row'] * scale
        c = tile_info['col'] * scale
        h = tile_info['h'] * scale
        w = tile_info['w'] * scale
        
        # Crop tile to actual size (remove padding)
        if channels > 0:
            if tile_data.ndim == 3 and tile_data.shape[0] in (1, 3, 4) and tile_data.shape[0] < tile_data.shape[1]:
                tile_data = np.transpose(tile_data, (1, 2, 0))
            tile_cropped = tile_data[:h, :w, :]
        else:
            tile_cropped = tile_data[:h, :w]
        
        # Clamp to output bounds
        out_h = min(h, output_h - r)
        out_w = min(w, output_w - c)
        
        if out_h <= 0 or out_w <= 0:
            continue
        
        # Create blending weight (linear feathering at edges)
        blend_w = _create_blend_weight(out_h, out_w, scaled_overlap)
        
        if channels > 0:
            output[r:r+out_h, c:c+out_w, :] += tile_cropped[:out_h, :out_w, :] * blend_w[:, :, np.newaxis]
        else:
            output[r:r+out_h, c:c+out_w] += tile_cropped[:out_h, :out_w] * blend_w
        weight_map[r:r+out_h, c:c+out_w] += blend_w
    
    # Normalize by weight
    weight_map = np.maximum(weight_map, 1e-8)
    if channels > 0:
        output /= weight_map[:, :, np.newaxis]
    else:
        output /= weight_map
    
    return output


def _create_blend_weight(h: int, w: int, overlap: int) -> np.ndarray:
    """Create a blending weight map with linear ramps at overlap regions.
    
    Center of tile gets weight 1.0, edges get linear ramp from 0 to 1.
    """
    if overlap <= 0:
        return np.ones((h, w), dtype=np.float32)
    
    ramp = min(overlap, h // 4, w // 4)
    if ramp <= 0:
        return np.ones((h, w), dtype=np.float32)
    
    weight = np.ones((h, w), dtype=np.float32)
    
    # Vertical ramps
    for i in range(ramp):
        alpha = (i + 1) / ramp
        weight[i, :] *= alpha
        weight[h - 1 - i, :] *= alpha
    
    # Horizontal ramps
    for j in range(ramp):
        alpha = (j + 1) / ramp
        weight[:, j] *= alpha
        weight[:, w - 1 - j] *= alpha
    
    return weight
