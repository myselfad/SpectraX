import os
import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np
import rasterio

class MultispectralDataset(Dataset):
    def __init__(self, data_dir, transform=None):
        self.data_dir = data_dir
        self.transform = transform
        # Expect pairs stored as LR and HR subdirectories or stacked TIFFs
        self.samples = [] 
        
    def __len__(self):
        return len(self.samples)
        
    def __getitem__(self, idx):
        # Stub implementation
        # return lr_tensor, hr_tensor
        return torch.zeros((4, 64, 64)), torch.zeros((4, 256, 256))

def get_dataloaders(config):
    train_ds = MultispectralDataset(config['data']['train_dir'])
    val_ds = MultispectralDataset(config['data']['val_dir'])
    
    train_dl = DataLoader(train_ds, batch_size=config['training']['batch_size'], shuffle=True, num_workers=config['training']['num_workers'])
    val_dl = DataLoader(val_ds, batch_size=config['training']['batch_size'], shuffle=False)
    
    return train_dl, val_dl
