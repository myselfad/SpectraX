"""Monte Carlo Dropout uncertainty estimation.

Runs multiple stochastic forward passes through the SR model with
dropout/drop-path enabled (model.train() mode) to estimate pixel-wise
prediction uncertainty.
"""

import numpy as np
import torch
from app.super_resolution.model import ModelManager

def run_mc_dropout(model_manager: ModelManager, image_rgb: np.ndarray,
                   num_passes: int = 10, target_scale: int = 4, tile_size: int = 48,
                   overlap: int = 8) -> dict:
    model = model_manager.model
    device = model_manager.device
    model_scale = 4
    
    H, W, C = image_rgb.shape
    out_H, out_W = H * model_scale, W * model_scale
    
    tensor = torch.from_numpy(image_rgb.transpose(2, 0, 1)).float().unsqueeze(0).to(device)
    predictions = []
    
    # Enable stochastic mode
    model.train()
    for i in range(num_passes):
        with torch.no_grad():
            output = model(tensor)
        result = output.squeeze(0).cpu().numpy().transpose(1, 2, 0)
        result = np.clip(result[:out_H, :out_W, :], 0.0, 1.0)
        predictions.append(result)
    model.eval()
    
    predictions_array = np.stack(predictions, axis=0)
    mean_prediction = np.mean(predictions_array, axis=0)
    std_prediction = np.std(predictions_array, axis=0)
    
    if target_scale != 4:
        import cv2
        new_h = int(mean_prediction.shape[0] * target_scale / 4)
        new_w = int(mean_prediction.shape[1] * target_scale / 4)
        mean_prediction = cv2.resize(mean_prediction, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
    uncertainty_map = np.mean(std_prediction, axis=-1)
    
    if target_scale != 4:
        import cv2
        new_h = int(uncertainty_map.shape[0] * target_scale / 4)
        new_w = int(uncertainty_map.shape[1] * target_scale / 4)
        uncertainty_map = cv2.resize(uncertainty_map, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    uncertainty_stats = {
        'min': float(np.min(uncertainty_map)),
        'max': float(np.max(uncertainty_map)),
        'mean': float(np.mean(uncertainty_map)),
        'median': float(np.median(uncertainty_map)),
    }
    
    # Reliability Calculation (Phase 8)
    max_u = uncertainty_stats['max']
    if max_u > 0:
        normalized_uncertainty = np.clip(uncertainty_map / max_u, 0.0, 1.0)
    else:
        normalized_uncertainty = uncertainty_map
        
    reliability_map = 1.0 - normalized_uncertainty
    
    # Threshold for high reliability (e.g. 0.8)
    threshold = 0.8
    high_rel_pixels = np.sum(reliability_map >= threshold)
    total_pixels = reliability_map.size
    high_rel_percentage = (high_rel_pixels / total_pixels) * 100.0
    
    reliability_stats = {
        'mean_score': float(np.mean(reliability_map)),
        'high_reliability_percentage': float(high_rel_percentage),
        'threshold': threshold
    }
    
    return {
        'mean_prediction': mean_prediction.astype(np.float32),
        'uncertainty_map': uncertainty_map.astype(np.float32),
        'reliability_map': reliability_map.astype(np.float32),
        'num_passes': num_passes,
        'method': 'MC-DropPath (Stochastic Depth)',
        'uncertainty_stats': uncertainty_stats,
        'reliability_stats': reliability_stats
    }
