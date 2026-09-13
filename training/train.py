import argparse
import yaml
import torch
import torch.nn as nn
import torch.optim as optim
from dataset import get_dataloaders
import os
import sys

# Add backend to path to import model
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))
from app.super_resolution.swinir_arch import SwinIR

def train(config_path):
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Training on {device}...")
    
    # Initialize Model (4 channels in, 4 out for native multispectral)
    model = SwinIR(
        upscale=config['model']['scale_factor'],
        in_chans=config['model']['in_channels'],
        img_size=48, window_size=8,
        img_range=1., depths=[6, 6, 6, 6, 6, 6], embed_dim=180, num_heads=[6, 6, 6, 6, 6, 6],
        mlp_ratio=2, upsampler='pixelshuffle', resi_connection='1conv'
    ).to(device)
    
    optimizer = optim.Adam(model.parameters(), lr=config['training']['learning_rate'])
    criterion_pixel = nn.L1Loss()
    
    # train_dl, val_dl = get_dataloaders(config)
    
    epochs = config['training']['epochs']
    scaler = torch.cuda.amp.GradScaler(enabled=config['training']['mixed_precision'])
    
    print("Starting training loop...")
    # for epoch in range(epochs):
    #     model.train()
    #     for lr, hr in train_dl:
    #         lr, hr = lr.to(device), hr.to(device)
    #         optimizer.zero_grad()
    #         with torch.cuda.amp.autocast(enabled=config['training']['mixed_precision']):
    #             sr = model(lr)
    #             loss = criterion_pixel(sr, hr)
    #         scaler.scale(loss).backward()
    #         scaler.step(optimizer)
    #         scaler.update()
            
    print("Training pipeline ready.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="config.yaml")
    args = parser.parse_args()
    train(args.config)
