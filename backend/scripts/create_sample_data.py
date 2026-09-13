"""Generate synthetic satellite imagery for testing and demonstration.

Creates a 4-band GeoTIFF (Blue, Green, Red, NIR) and a 3-band PNG fallback.
The imagery contains synthetic terrain-like features (gradients, noise, blobs)
to visually verify super-resolution performance.
"""

import os
import numpy as np
from PIL import Image

def generate_terrain_pattern(height, width):
    """Generate a synthetic terrain-like pattern."""
    x = np.linspace(0, 10, width)
    y = np.linspace(0, 10, height)
    xx, yy = np.meshgrid(x, y)
    
    # Low frequency structural features
    base = np.sin(xx) * np.cos(yy) * 0.5 + 0.5
    
    # Add some "urban" or "field" rectangular blobs
    blobs = np.zeros((height, width))
    blobs[height//4:height//2, width//4:width//2] = 0.8
    blobs[height//2:height*3//4, width*3//4:width*7//8] = 0.6
    
    # Add high frequency noise (simulating texture)
    noise = np.random.normal(0, 0.1, (height, width))
    
    pattern = base * 0.6 + blobs * 0.3 + noise
    return np.clip(pattern, 0, 1)

def create_sample():
    # Ensure data dir exists
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    height, width = 256, 256
    
    # Generate base patterns
    terrain = generate_terrain_pattern(height, width)
    vegetation = generate_terrain_pattern(height, width)[::-1, :] # flipped pattern
    
    # Create bands
    # Red: inverse of vegetation
    red = np.clip(terrain - vegetation * 0.5, 0, 1)
    # Green: mix of terrain and vegetation
    green = np.clip(terrain * 0.5 + vegetation * 0.5, 0, 1)
    # Blue: mostly uniform with some noise (atmospheric scattering simulation)
    blue = np.clip(terrain * 0.3 + np.random.normal(0.2, 0.05, (height, width)), 0, 1)
    # NIR: highly correlated with vegetation
    nir = np.clip(vegetation + terrain * 0.2, 0, 1)
    
    # Normalize bands to [0, 1] for saving
    red = (red - red.min()) / (red.max() - red.min())
    green = (green - green.min()) / (green.max() - green.min())
    blue = (blue - blue.min()) / (blue.max() - blue.min())
    nir = (nir - nir.min()) / (nir.max() - nir.min())
    
    # 1. Save 4-band GeoTIFF
    tif_path = os.path.join(data_dir, 'demo_sample.tif')
    try:
        import rasterio
        from rasterio.transform import from_origin
        
        # Stack as CHW: Blue, Green, Red, NIR (Sentinel-2 order)
        tif_data = np.stack([blue, green, red, nir], axis=0)
        
        # Scale to uint16
        tif_data_uint16 = (tif_data * 65535).astype(np.uint16)
        
        # Define geospatial metadata
        transform = from_origin(500000.0, 4600000.0, 10.0, 10.0) # 10m resolution
        crs = 'EPSG:32643' # WGS 84 / UTM zone 43N
        
        with rasterio.open(
            tif_path,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=4,
            dtype=tif_data_uint16.dtype,
            crs=crs,
            transform=transform,
        ) as dst:
            dst.write(tif_data_uint16)
            dst.set_band_description(1, 'Blue')
            dst.set_band_description(2, 'Green')
            dst.set_band_description(3, 'Red')
            dst.set_band_description(4, 'NIR')
            
        print(f"Created 4-band GeoTIFF: {tif_path}")
    except ImportError:
        print("Rasterio not available, skipping GeoTIFF creation.")
        
    # 2. Save 3-band PNG
    png_path = os.path.join(data_dir, 'demo_sample.png')
    # RGB stack for PNG
    rgb_data = np.stack([red, green, blue], axis=-1)
    rgb_uint8 = (rgb_data * 255).astype(np.uint8)
    Image.fromarray(rgb_uint8).save(png_path)
    print(f"Created 3-band PNG: {png_path}")

if __name__ == "__main__":
    create_sample()
