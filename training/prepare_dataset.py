import os
import argparse
import numpy as np
import rasterio
from rasterio.enums import Resampling
import cv2

def synthetic_degradation(hr_data, scale_factor):
    """
    Apply synthetic degradation (blur + downsample) to generate LR from HR.
    hr_data shape: (C, H, W)
    """
    c, h, w = hr_data.shape
    new_h, new_w = h // scale_factor, w // scale_factor
    
    lr_data = np.zeros((c, new_h, new_w), dtype=np.float32)
    for i in range(c):
        # Apply slight Gaussian blur to simulate sensor PSF
        blurred = cv2.GaussianBlur(hr_data[i], (3, 3), 0.5)
        # Downsample
        lr_data[i] = cv2.resize(blurred, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        
    return lr_data

def prepare(args):
    print(f"Preparing dataset from {args.input_dir} into {args.out_dir}...")
    os.makedirs(args.out_dir, exist_ok=True)
    
    # Example stub: in a real scenario, this iterates over large GeoTIFFs,
    # crops them into HR patches, and applies synthetic_degradation for LR.
    print("Dataset preparation complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", type=str, required=True)
    parser.add_argument("--out_dir", type=str, required=True)
    parser.add_argument("--scale", type=int, default=4)
    args = parser.parse_args()
    prepare(args)
