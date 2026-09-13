import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MODEL_PATH: str = './weights/swinir_classical_sr_x4.pth'
    DATA_DIR: str = './data'
    OUTPUT_DIR: str = './output'
    UPLOAD_DIR: str = './uploads'
    HOST: str = '0.0.0.0'
    PORT: int = 8000
    MAX_FILE_SIZE_MB: int = 100
    DEFAULT_SCALE_FACTOR: int = 4
    DEFAULT_UNCERTAINTY_PASSES: int = 10
    DEFAULT_PATCH_SIZE: int = 48
    DEFAULT_PATCH_OVERLAP: int = 8
    ALLOWED_EXTENSIONS: list = ['.tif', '.tiff', '.png', '.jpg', '.jpeg']

    # AWS S3 Storage Configuration
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_SESSION_TOKEN: str | None = None
    AWS_REGION: str = 'ap-south-1'
    AWS_S3_BUCKET_NAME: str = 'spectrax-sih2026-storage'
    AWS_S3_ENABLED: bool = False
    AWS_S3_PRESIGNED_EXPIRY: int = 3600

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Create directories on startup
for path in [settings.DATA_DIR, settings.OUTPUT_DIR, settings.UPLOAD_DIR]:
    os.makedirs(path, exist_ok=True)
