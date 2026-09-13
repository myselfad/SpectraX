import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch
from app.core.config import Settings
from app.services.s3_storage import S3StorageService


def test_s3_service_disabled_by_default():
    """Verify S3 service degrades gracefully when disabled."""
    service = S3StorageService()
    service.enabled = False
    
    assert service.is_available() is False
    assert service.check_bucket_exists() is False
    assert service.upload_file("dummy.txt", "dummy_key") is None
    assert service.download_file("dummy_key", "dummy.txt") is False
    assert service.generate_presigned_url("dummy_key") is None


def test_s3_mock_create_private_bucket():
    """Verify create_private_bucket configures Block Public Access and SSE-S3 encryption."""
    mock_boto_client = MagicMock()
    
    service = S3StorageService()
    service.enabled = True
    service._s3_client = mock_boto_client
    service.bucket_name = "spectrax-sih2026-storage"
    service.region = "ap-south-1"

    success = service.create_private_bucket("spectrax-sih2026-storage", "ap-south-1")
    assert success is True

    # 1. Bucket creation
    mock_boto_client.create_bucket.assert_called_once_with(
        Bucket="spectrax-sih2026-storage",
        CreateBucketConfiguration={"LocationConstraint": "ap-south-1"}
    )

    # 2. Block Public Access verification
    mock_boto_client.put_public_access_block.assert_called_once_with(
        Bucket="spectrax-sih2026-storage",
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True
        }
    )

    # 3. Default encryption verification
    mock_boto_client.put_bucket_encryption.assert_called_once_with(
        Bucket="spectrax-sih2026-storage",
        ServerSideEncryptionConfiguration={
            "Rules": [
                {
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }
            ]
        }
    )


def test_s3_mock_upload_and_presigned_url():
    """Verify upload_file and presigned URL generation."""
    mock_boto_client = MagicMock()
    mock_boto_client.generate_presigned_url.return_value = "https://s3.ap-south-1.amazonaws.com/spectrax-sih2026-storage/outputs/test_job/sr_output.png?signature=xyz"

    service = S3StorageService()
    service.enabled = True
    service._s3_client = mock_boto_client
    service.bucket_name = "spectrax-sih2026-storage"

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
        tf.write(b"fake_image_bytes")
        temp_path = tf.name

    try:
        s3_uri = service.upload_file(temp_path, "outputs/test_job/sr_output.png")
        assert s3_uri == "s3://spectrax-sih2026-storage/outputs/test_job/sr_output.png"
        mock_boto_client.upload_file.assert_called_once()

        url = service.generate_presigned_url("outputs/test_job/sr_output.png")
        assert url is not None
        assert "signature=xyz" in url
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
