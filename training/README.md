# SpectraX Training Pipeline

This directory contains the reproducible training and fine-tuning pipeline for the SpectraX Multispectral Super Resolution model.

## Structure
- `config.yaml`: Configuration for datasets, model hyperparameters, and training loops.
- `prepare_dataset.py`: Script to generate LR-HR pairs from high-resolution multispectral imagery via synthetic degradation.
- `dataset.py`: PyTorch `Dataset` and `DataLoader` definitions for 4-channel imagery.
- `train.py`: Main training loop with mixed-precision, checkpoint saving, and validation.
- `validate.py`: Independent validation script to compute PSNR/SSIM/Spectral metrics on a test set.

## Requirements
Ensure you have the backend dependencies installed (PyTorch, Rasterio, etc.).

## Usage

1. **Prepare Data**
   ```bash
   python prepare_dataset.py --input_dir /path/to/raw/sentinel --out_dir ./data/pairs
   ```

2. **Train Model**
   ```bash
   python train.py --config config.yaml
   ```

3. **Validate Checkpoint**
   ```bash
   python validate.py --checkpoint checkpoints/best_model.pth --data_dir ./data/pairs/val
   ```
