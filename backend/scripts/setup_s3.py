#!/usr/bin/env python3
"""AWS S3 Setup and Resource Inspection Script for SpectraX.

Usage:
    python scripts/setup_s3.py [--create] [--region ap-south-1] [--bucket spectrax-sih2026-storage]

Features:
- Inspects available AWS credentials and STS caller identity.
- Lists existing S3 buckets in the account to discover whether an appropriate bucket already exists.
- Creates a private bucket with Block Public Access (all 4 rules enabled) and AES256 encryption if not found.
- Performs end-to-end verification (upload -> presigned URL -> download -> delete test key).
- Zero exposure of secret keys.
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.services.s3_storage import s3_storage, S3StorageService

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    print("❌ Error: boto3 is not installed. Please run: pip install boto3 botocore")
    sys.exit(1)


def inspect_aws_environment(region: str):
    """Check AWS credentials and caller identity."""
    print("=" * 65)
    print("🛰️  SpectraX - AWS Environment Inspection")
    print("=" * 65)

    client_kwargs = {"region_name": region}
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        client_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        client_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
        if settings.AWS_SESSION_TOKEN:
            client_kwargs["aws_session_token"] = settings.AWS_SESSION_TOKEN
        print("🔑 Using explicit credentials from configuration/environment.")
    else:
        print("🔑 Using standard AWS credential chain (~/.aws, env vars, or IAM role).")

    try:
        sts_client = boto3.client("sts", **client_kwargs)
        caller = sts_client.get_caller_identity()
        print(f"✅ Authenticated to AWS successfully!")
        print(f"   • Account ID: {caller.get('Account')}")
        print(f"   • Principal ARN: {caller.get('Arn')}")
        print(f"   • User ID: {caller.get('UserId')}")
        print(f"   • Configured Region: {region}")
        return client_kwargs
    except NoCredentialsError:
        print("❌ No AWS credentials found.")
        print("   Please configure your AWS credentials using one of:")
        print("   1. Add AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to backend/.env")
        print("   2. Run 'aws configure' in terminal")
        print("   3. Export AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in your shell")
        return None
    except ClientError as e:
        print(f"❌ Failed to verify AWS caller identity: {e}")
        return None


def inspect_s3_buckets(client_kwargs: dict):
    """List accessible buckets in the account."""
    print("\n📦 Inspecting S3 Buckets in Account...")
    s3_client = boto3.client("s3", **client_kwargs)

    try:
        response = s3_client.list_buckets()
        buckets = [b["Name"] for b in response.get("Buckets", [])]
        print(f"Found {len(buckets)} bucket(s) in this account:")
        for b in buckets:
            highlight = " (⭐ matches project)" if "spectrax" in b.lower() or "sih" in b.lower() else ""
            print(f"   • {b}{highlight}")
        return buckets
    except ClientError as e:
        print(f"⚠️ Could not list all buckets (lacking s3:ListAllMyBuckets or permission restricted): {e}")
        return []


def ensure_private_bucket(s3_client, bucket_name: str, region: str, auto_create: bool = True):
    """Check target bucket or create a strictly private one."""
    print(f"\n🔒 Target Project Bucket: '{bucket_name}' in region '{region}'")

    # 1. Check if bucket exists
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ Bucket '{bucket_name}' already exists and is accessible.")
        return True
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code in ("404", "NoSuchBucket"):
            print(f"ℹ️ Bucket '{bucket_name}' does not exist yet.")
        elif error_code == "403":
            print(f"❌ Bucket '{bucket_name}' exists but access is forbidden (belongs to another account or IAM denied).")
            return False
        else:
            print(f"⚠️ head_bucket check returned: {e}")

    if not auto_create:
        print(f"ℹ️ Auto-creation is disabled. Run with --create to create '{bucket_name}'.")
        return False

    # 2. Create the private bucket
    print(f"🛠️ Creating private bucket '{bucket_name}'...")
    try:
        if region == "us-east-1":
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region}
            )
        print(f"✅ S3 bucket '{bucket_name}' created successfully!")

        # 3. Apply Block Public Access
        print("🛡️ Applying Block Public Access (all 4 rules enabled)...")
        s3_client.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True
            }
        )
        print("✅ All public access is strictly blocked.")

        # 4. Apply Default Encryption
        print("🔐 Configuring default Server-Side Encryption (AES256)...")
        s3_client.put_bucket_encryption(
            Bucket=bucket_name,
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
        print("✅ Default server-side encryption enabled.")
        return True

    except ClientError as e:
        print(f"❌ Failed to create bucket '{bucket_name}': {e}")
        return False


def verify_s3_pipeline(s3_client, bucket_name: str):
    """Run an end-to-end verification test."""
    print("\n🧪 Running S3 Integration Verification Test...")
    test_key = "test/spectrax_s3_verification.json"
    test_data = {
        "project": "SpectraX",
        "description": "Verification payload for S3 private cloud storage",
        "version": "1.0.0"
    }

    try:
        # Upload
        s3_client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=json.dumps(test_data),
            ContentType="application/json"
        )
        print(f"   [1/4] ✅ Uploaded test object to s3://{bucket_name}/{test_key}")

        # Presigned URL
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket_name, "Key": test_key},
            ExpiresIn=300
        )
        print(f"   [2/4] ✅ Generated presigned download URL (valid for 5 mins)")

        # Read back
        response = s3_client.get_object(Bucket=bucket_name, Key=test_key)
        downloaded = json.loads(response["Body"].read().decode("utf-8"))
        assert downloaded["project"] == "SpectraX"
        print(f"   [3/4] ✅ Verified object integrity on read-back")

        # Cleanup test object
        s3_client.delete_object(Bucket=bucket_name, Key=test_key)
        print(f"   [4/4] ✅ Cleaned up verification test object")

        print("\n🎉 S3 Storage is fully configured, verified, and operational!")
        return True
    except Exception as e:
        print(f"❌ Verification test failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="SpectraX AWS S3 Storage Setup & Inspection")
    parser.add_argument("--create", action="store_true", default=True, help="Create bucket if not existing")
    parser.add_argument("--bucket", default=settings.AWS_S3_BUCKET_NAME, help="Bucket name")
    parser.add_argument("--region", default=settings.AWS_REGION, help="AWS region")
    args = parser.parse_args()

    client_kwargs = inspect_aws_environment(region=args.region)
    if not client_kwargs:
        sys.exit(1)

    inspect_s3_buckets(client_kwargs)
    s3_client = boto3.client("s3", **client_kwargs)

    success = ensure_private_bucket(s3_client, args.bucket, args.region, auto_create=args.create)
    if success:
        verify_s3_pipeline(s3_client, args.bucket)
        print("\n💡 To enable S3 in the SpectraX backend, set in backend/.env:")
        print("   AWS_S3_ENABLED=true")
        print(f"   AWS_S3_BUCKET_NAME={args.bucket}")
        print(f"   AWS_REGION={args.region}")


if __name__ == "__main__":
    main()
