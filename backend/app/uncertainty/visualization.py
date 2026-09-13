"""Uncertainty heatmap visualization.

Creates publication-quality heatmaps using matplotlib colormaps.
"""

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm

def save_heatmap_visualization(data_map: np.ndarray, output_path: str,
                                colormap: str = 'hot', title: str = 'Map',
                                cbar_label: str = 'Value', stats: dict = None):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#0f172a')
    
    im = ax.imshow(data_map, cmap=colormap, interpolation='bilinear')
    
    ax.set_title(title, fontsize=14, fontweight='bold', color='white', pad=15)
    ax.axis('off')
    
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(cbar_label, fontsize=11, color='white')
    cbar.ax.yaxis.set_tick_params(color='white')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
    
    if stats:
        stats_text = (
            f"Min: {stats.get('min', 0):.4f}  |  "
            f"Max: {stats.get('max', 0):.4f}  |  "
            f"Mean: {stats.get('mean', 0):.4f}"
        )
        ax.text(0.5, -0.02, stats_text, transform=ax.transAxes,
                fontsize=10, color='#94a3b8', ha='center', va='top',
                fontfamily='monospace')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#0f172a', edgecolor='none')
    plt.close(fig)

def save_uncertainty_visualization(uncertainty_map: np.ndarray, output_path: str, stats: dict = None):
    save_heatmap_visualization(uncertainty_map, output_path, 'hot', 'Pixel-wise Prediction Uncertainty (Std Dev)', 'Uncertainty (σ)', stats)
