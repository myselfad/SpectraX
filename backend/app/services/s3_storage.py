"""AWS S3 Storage Service for SpectraX Satellite Super-Resolution.

Handles cloud storage for raw satellite imagery (GeoTIFF/multispectral),
SR outputs, uncertainty heatmaps, reliability maps, and validation metrics.

Key Security Principles:
- Strictly private buckets (all public access blocked)
- Default Server-Side Encryption (AES256)
- Least-privilege operations
- Zero credential leakage (credentials loaded from environment or IAM roles)
- Graceful degradation if S3 is disabled or unconfigured
"""

import os
import mimetypes
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger("spectrax.s3")

try:
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    ClientError = Exception
    BotoCoreError = Exception

from app.core.config import settings


class S3StorageService:
    """Service to interact with AWS S3 in a secure, private, and resilient manner."""

    _instance: Optional["S3StorageService"] = None

    def __init__(self):
        self.bucket_name = settings.AWS_S3_BUCKET_NAME
        self.region = settings.AWS_REGION
        self.enabled = settings.AWS_S3_ENABLED and BOTO3_AVAILABLE
        self._s3_client = None
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "S3StorageService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def client(self):
        """Lazy-initialize and return the boto3 S3 client."""
        if not BOTO3_AVAILABLE:
            return None

        if self._s3_client is None:
            client_kwargs: Dict[str, Any] = {"region_name": self.region}

            # If explicit credentials are provided in settings/env, use them;
            # otherwise boto3 will automatically discover IAM role or ~/.aws
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                client_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                client_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
                if settings.AWS_SESSION_TOKEN:
                    client_kwargs["aws_session_token"] = settings.AWS_SESSION_TOKEN

            try:
                self._s3_client = boto3.client("s3", **client_kwargs)
                self._initialized = True
            except Exception as e:
                logger.warning(f"Failed to initialize S3 client: {e}")
                self._s3_client = None
                self.enabled = False

        return self._s3_client

    def is_available(self) -> bool:
        """Check if S3 storage is enabled and the client can be initialized."""
        return bool(self.enabled and self.client is not None)

    def check_bucket_exists(self, bucket_name: Optional[str] = None) -> bool:
        """Verify whether the designated S3 bucket exists and is accessible."""
        target_bucket = bucket_name or self.bucket_name
        if not self.is_available():
            return False

        try:
            self.client.head_bucket(Bucket=target_bucket)
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code in ("404", "NoSuchBucket"):
                logger.info(f"S3 bucket '{target_bucket}' does not exist.")
            elif error_code == "403":
                logger.warning(f"Access to S3 bucket '{target_bucket}' is forbidden (403).")
            else:
                logger.warning(f"S3 head_bucket check failed: {e}")
            return False
        except Exception as e:
            logger.warning(f"Error checking bucket existence: {e}")
            return False

    def create_private_bucket(self, bucket_name: Optional[str] = None, region: Optional[str] = None) -> bool:
        """Create a private S3 bucket with Block Public Access and SSE-S3 encryption enabled.
        
        Strictly prevents any public access to imagery or results.
        """
        target_bucket = bucket_name or self.bucket_name
        target_region = region or self.region

        if not self.is_available():
            logger.warning("Cannot create bucket: S3 service is not available.")
            return False

        try:
            # S3 API distinction: us-east-1 requires omitting LocationConstraint
            if target_region == "us-east-1":
                self.client.create_bucket(Bucket=target_bucket)
            else:
                self.client.create_bucket(
                    Bucket=target_bucket,
                    CreateBucketConfiguration={"LocationConstraint": target_region}
                )
            logger.info(f"Created S3 bucket '{target_bucket}' in region '{target_region}'.")

            # 1. Enforce Block Public Access (all 4 settings enabled)
            self.client.put_public_access_block(
                Bucket=target_bucket,
                PublicAccessBlockConfiguration={
                    "BlockPublicAcls": True,
                    "IgnorePublicAcls": True,
                    "BlockPublicPolicy": True,
                    "RestrictPublicBuckets": True
                }
            )
            logger.info(f"Enabled Block Public Access for '{target_bucket}'.")

            # 2. Enforce default Server-Side Encryption (AES256)
            self.client.put_bucket_encryption(
                Bucket=target_bucket,
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
            logger.info(f"Configured default AES256 server-side encryption for '{target_bucket}'.")
            return True

        except ClientError as e:
            logger.error(f"Failed to create private bucket '{target_bucket}': {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating bucket '{target_bucket}': {e}")
            return False

    def upload_file(
        self,
        local_path: str,
        s3_key: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """Upload a local file to S3.
        
        Returns the S3 URI (s3://bucket/key) upon success, or None on failure.
        """
        if not self.is_available():
            return None

        if not os.path.exists(local_path):
            logger.warning(f"Local file does not exist for S3 upload: {local_path}")
            return None

        # Determine content type if not provided
        if not content_type:
            content_type, _ = mimetypes.guess_type(local_path)
            if not content_type:
                if local_path.endswith((".tif", ".tiff")):
                    content_type = "image/tiff"
                elif local_path.endswith(".png"):
                    content_type = "image/png"
                elif local_path.endswith(".json"):
                    content_type = "application/json"
                else:
                    content_type = "application/octet-stream"

        extra_args: Dict[str, Any] = {"ContentType": content_type}
        if metadata:
            extra_args["Metadata"] = metadata

        try:
            self.client.upload_file(
                Filename=local_path,
                Bucket=self.bucket_name,
                Key=s3_key,
                ExtraArgs=extra_args
            )
            s3_uri = f"s3://{self.bucket_name}/{s3_key}"
            logger.info(f"Uploaded {local_path} -> {s3_uri}")
            return s3_uri
        except Exception as e:
            logger.error(f"Failed to upload {local_path} to S3 ({s3_key}): {e}")
            return None

    def download_file(self, s3_key: str, local_path: str) -> bool:
        """Download an object from S3 to a local destination."""
        if not self.is_available():
            return False

        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self.client.download_file(
                Bucket=self.bucket_name,
                Key=s3_key,
                Filename=local_path
            )
            logger.info(f"Downloaded s3://{self.bucket_name}/{s3_key} -> {local_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download s3://{self.bucket_name}/{s3_key}: {e}")
            return False

    def generate_presigned_url(
        self,
        s3_key: str,
        expires_in: Optional[int] = None,
        http_method: str = "get_object"
    ) -> Optional[str]:
        """Generate a secure, time-limited presigned URL for private S3 objects."""
        if not self.is_available():
            return None

        expiration = expires_in or settings.AWS_S3_PRESIGNED_EXPIRY

        try:
            url = self.client.generate_presigned_url(
                ClientMethod=http_method,
                Params={
                    "Bucket": self.bucket_name,
                    "Key": s3_key
                },
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {s3_key}: {e}")
            return None

    def upload_job_file(
        self,
        job_id: str,
        local_path: str,
        filename: str,
        category: str = "outputs"
    ) -> Dict[str, Any]:
        """Helper to upload a job artifact (upload or output) and return its S3 metadata."""
        s3_key = f"{category}/{job_id}/{filename}"
        s3_uri = self.upload_file(local_path=local_path, s3_key=s3_key)
        presigned_url = None
        if s3_uri:
            presigned_url = self.generate_presigned_url(s3_key)

        return {
            "s3_key": s3_key if s3_uri else None,
            "s3_uri": s3_uri,
            "presigned_url": presigned_url,
            "bucket": self.bucket_name if s3_uri else None
        }


# Singleton accessor
s3_storage = S3StorageService.get_instance()
