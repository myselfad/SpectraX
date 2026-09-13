import os
import torch
import torch.nn as nn

class ModelManager:
    _instance = None
    _model = None
    _device = None
    _loaded = False
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def load_model(self, model_path: str, device: str = None) -> bool:
        try:
            from app.super_resolution.swinir_arch import build_swinir
            if device is None:
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self._device = torch.device(device)
            
            self._model = build_swinir(upscale=4, in_chans=3)
            
            if os.path.exists(model_path):
                state_dict = torch.load(model_path, map_location=self._device)
                if 'params' in state_dict:
                    state_dict = state_dict['params']
                elif 'params_ema' in state_dict:
                    state_dict = state_dict['params_ema']
                self._model.load_state_dict(state_dict, strict=True)
                self._loaded = True
            else:
                self._loaded = False
                
            self._model.to(self._device)
            self._model.eval()
        except ImportError:
            self._loaded = False
        return self._loaded
    
    @property
    def model(self):
        return self._model
    
    @property  
    def device(self):
        return self._device
    
    @property
    def is_loaded(self):
        return self._loaded
    
    def get_info(self) -> dict:
        return {
            'model_name': 'SwinIR-M Classical SR',
            'model_type': 'Swin Transformer',
            'scale_factor': 4,
            'input_channels': 3,
            'pretrained': self._loaded,
            'device': str(self._device),
            'parameters': sum(p.numel() for p in self._model.parameters()) if self._model else 0
        }
