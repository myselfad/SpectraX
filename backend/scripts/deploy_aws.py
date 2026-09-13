#!/usr/bin/env python3
"""Automated Full AWS Deployment Script for SpectraX.

Provisions and configures:
1. S3 bucket policy (makes outputs/* publicly readable with CORS enabled, keeps uploads/* private).
2. IAM Role & Instance Profile for EC2 with least-privilege S3 access.
3. Security Group with HTTP (port 80) and SSH (port 22).
4. Ubuntu 24.04 EC2 instance (t3.medium) with automated cloud-init.
5. Nginx reverse-proxy & systemd service for FastAPI backend.
"""

import sys
import time
import json
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("❌ Error: boto3 is not installed.")
    sys.exit(1)


def get_aws_clients():
    session_kwargs = {
        "region_name": settings.AWS_REGION,
        "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
    }
    if settings.AWS_SESSION_TOKEN:
        session_kwargs["aws_session_token"] = settings.AWS_SESSION_TOKEN

    ec2 = boto3.client("ec2", **session_kwargs)
    s3 = boto3.client("s3", **session_kwargs)
    iam = boto3.client("iam", **session_kwargs)
    return ec2, s3, iam


def configure_s3_public_outputs(s3, bucket_name: str):
    """Allow public read on outputs/* prefix while keeping uploads/* private."""
    print("\n🌐 Step 1: Configuring S3 Permissions & Public Access for outputs/*...")

    try:
        # 1. Update Public Access Block to allow bucket policies
        s3.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": False,
                "RestrictPublicBuckets": False,
            },
        )
        print("   ✅ Configured Public Access Block (bucket policies allowed).")

        # 2. Attach Bucket Policy for public read on outputs/*
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadOutputs",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/outputs/*",
                }
            ],
        }
        s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(bucket_policy))
        print(f"   ✅ Attached public read policy for s3://{bucket_name}/outputs/*")

        # 3. Configure CORS
        cors_config = {
            "CORSRules": [
                {
                    "AllowedHeaders": ["*"],
                    "AllowedMethods": ["GET", "HEAD"],
                    "AllowedOrigins": ["*"],
                    "ExposeHeaders": [],
                    "MaxAgeSeconds": 3000,
                }
            ]
        }
        s3.put_bucket_cors(Bucket=bucket_name, CORSConfiguration=cors_config)
        print("   ✅ Enabled S3 CORS for global image access.")
        return True
    except ClientError as e:
        print(f"   ⚠️ S3 policy configuration error: {e}")
        return False


def setup_iam_role(iam, bucket_name: str):
    """Create IAM role and instance profile for EC2 to access S3."""
    print("\n🔑 Step 2: Configuring IAM Role & Instance Profile for EC2...")
    role_name = "spectrax-ec2-s3-role"
    profile_name = "spectrax-ec2-profile"

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "ec2.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }

    # 1. Create or get Role
    try:
        iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Role for SpectraX EC2 instance to access S3 storage",
        )
        print(f"   ✅ Created IAM Role: {role_name}")
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"   ℹ️ IAM Role {role_name} already exists.")

    # 2. Attach S3 Policy
    s3_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:DeleteObject",
                    "s3:ListBucket",
                ],
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*",
                ],
            }
        ],
    }
    try:
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName="SpectraXS3Access",
            PolicyDocument=json.dumps(s3_policy),
        )
        print("   ✅ Attached least-privilege S3 policy to role.")
    except ClientError as e:
        print(f"   ⚠️ Failed to put role policy: {e}")

    # 3. Create or get Instance Profile
    try:
        iam.create_instance_profile(InstanceProfileName=profile_name)
        print(f"   ✅ Created Instance Profile: {profile_name}")
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"   ℹ️ Instance Profile {profile_name} already exists.")

    # 4. Add role to instance profile
    try:
        iam.add_role_to_instance_profile(
            InstanceProfileName=profile_name, RoleName=role_name
        )
        print(f"   ✅ Added {role_name} to {profile_name}.")
    except iam.exceptions.LimitExceededException:
        pass
    except ClientError as e:
        if "Cannot exceed quota" in str(e) or "already exists" in str(e):
            pass
        else:
            print(f"   ℹ️ Role already in instance profile or: {e}")

    return profile_name


def setup_security_group(ec2):
    """Create or get security group allowing HTTP (80) and SSH (22)."""
    print("\n🛡️ Step 3: Configuring Security Group (HTTP & SSH)...")
    sg_name = "spectrax-web-sg"

    # Find default VPC
    vpcs = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])[
        "Vpcs"
    ]
    if not vpcs:
        raise RuntimeError("No default VPC found in region.")
    vpc_id = vpcs[0]["VpcId"]

    # Check if SG already exists
    sgs = ec2.describe_security_groups(
        Filters=[
            {"Name": "group-name", "Values": [sg_name]},
            {"Name": "vpc-id", "Values": [vpc_id]},
        ]
    )["SecurityGroups"]

    if sgs:
        sg_id = sgs[0]["GroupId"]
        print(f"   ℹ️ Security Group {sg_name} already exists: {sg_id}")
        return sg_id

    # Create SG
    res = ec2.create_security_group(
        GroupName=sg_name,
        Description="SpectraX Web Server SG (HTTP & SSH)",
        VpcId=vpc_id,
    )
    sg_id = res["GroupId"]
    print(f"   ✅ Created Security Group: {sg_id}")

    # Authorize ingress rules
    ip_permissions = [
        {
            "IpProtocol": "tcp",
            "FromPort": 80,
            "ToPort": 80,
            "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "HTTP Web Access"}],
        },
        {
            "IpProtocol": "tcp",
            "FromPort": 22,
            "ToPort": 22,
            "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "SSH Admin Access"}],
        },
    ]
    ec2.authorize_security_group_ingress(
        GroupId=sg_id, IpPermissions=ip_permissions
    )
    print("   ✅ Authorized inbound rules: Port 80 (HTTP) & Port 22 (SSH).")
    return sg_id


def generate_user_data(bucket_name: str, region: str) -> str:
    """Generate cloud-init bash script to configure and start the server."""
    script = f"""#!/bin/bash
set -e
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo "=== SpectraX Cloud Deployment Initializing ==="

# 1. Update and install system dependencies
export DEBIAN_FRONTEND=noninteractive

# Configure 4GB swapfile to ensure ample memory for PyTorch & npm build
if [ ! -f /swapfile ]; then
    fallocate -l 4G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=4096
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

apt-get update -y
apt-get install -y nginx git curl build-essential python3 python3-pip python3-venv libgl1-mesa-glx libglib2.0-0

# 2. Install Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# 3. Clone SpectraX Repository
mkdir -p /var/www
cd /var/www
git clone https://github.com/myselfad/SpectraX.git spectrax
cd /var/www/spectrax

# 4. Configure Backend Environment
cat << 'EOF' > /var/www/spectrax/backend/.env
MODEL_PATH=./weights/swinir_classical_sr_x4.pth
DATA_DIR=./data
OUTPUT_DIR=./output
UPLOAD_DIR=./uploads
HOST=127.0.0.1
PORT=8000
MAX_FILE_SIZE_MB=100
DEFAULT_SCALE_FACTOR=4
DEFAULT_UNCERTAINTY_PASSES=10
DEFAULT_PATCH_SIZE=48
DEFAULT_PATCH_OVERLAP=8
AWS_S3_ENABLED=true
AWS_S3_BUCKET_NAME={bucket_name}
AWS_REGION={region}
AWS_S3_PRESIGNED_EXPIRY=3600
EOF

# 5. Build Python Virtual Environment & Install Requirements
cd /var/www/spectrax/backend
python3 -m venv venv
/var/www/spectrax/backend/venv/bin/pip install --upgrade pip
/var/www/spectrax/backend/venv/bin/pip install -r requirements.txt

# 6. Build Frontend
cd /var/www/spectrax/frontend
npm install
npm run build

# 7. Configure Systemd Service for FastAPI
cat << 'EOF' > /etc/systemd/system/spectrax-backend.service
[Unit]
Description=SpectraX FastAPI AI Backend
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/spectrax/backend
ExecStart=/var/www/spectrax/backend/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable spectrax-backend
systemctl start spectrax-backend

# 8. Configure Nginx
cat << 'EOF' > /etc/nginx/sites-available/spectrax
server {{
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 100M;

    # Frontend Single Page App
    location / {{
        root /var/www/spectrax/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }}

    # Backend API Proxy
    location /api/ {{
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }}
}}
EOF

rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/spectrax /etc/nginx/sites-enabled/spectrax
nginx -t
systemctl restart nginx

echo "=== SpectraX Cloud Deployment Completed Successfully! ==="
"""
    return script


def launch_ec2_instance(ec2, sg_id: str, profile_name: str, bucket_name: str, region: str):
    """Launch Ubuntu 24.04 t3.medium EC2 instance."""
    print("\n🚀 Step 4: Launching EC2 Instance (t3.medium in ap-south-1)...")

    # Ubuntu 24.04 LTS AMI in ap-south-1
    ami_id = "ami-0c0fd09cfe77b59dc"
    instance_type = "t3.small"
    user_data = generate_user_data(bucket_name, region)

    # Wait a few seconds for IAM profile propagation
    print("   ⏳ Allowing IAM profile to propagate across AWS...")
    time.sleep(10)

    try:
        response = ec2.run_instances(
            ImageId=ami_id,
            InstanceType=instance_type,
            MinCount=1,
            MaxCount=1,
            SecurityGroupIds=[sg_id],
            IamInstanceProfile={"Name": profile_name},
            UserData=user_data,
            BlockDeviceMappings=[
                {
                    "DeviceName": "/dev/sda1",
                    "Ebs": {
                        "VolumeSize": 25,
                        "VolumeType": "gp3",
                        "DeleteOnTermination": True,
                    },
                }
            ],
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {"Key": "Name", "Value": "SpectraX-Production-Server"},
                        {"Key": "Project", "Value": "SpectraX"},
                    ],
                }
            ],
        )

        instance_id = response["Instances"][0]["InstanceId"]
        print(f"   ✅ Launched EC2 Instance: {instance_id}")

        # Wait for instance running
        print("   ⏳ Waiting for EC2 instance to initialize and receive Public IP...")
        waiter = ec2.get_waiter("instance_running")
        waiter.wait(InstanceIds=[instance_id])

        desc = ec2.describe_instances(InstanceIds=[instance_id])
        inst = desc["Reservations"][0]["Instances"][0]
        public_ip = inst.get("PublicIpAddress")
        public_dns = inst.get("PublicDnsName")

        print(f"   🎉 EC2 Instance is RUNNING!")
        print(f"   • Public IP:  {public_ip}")
        print(f"   • Public DNS: {public_dns}")
        return instance_id, public_ip, public_dns

    except ClientError as e:
        print(f"❌ Failed to launch EC2 instance: {e}")
        sys.exit(1)


def main():
    print("=" * 65)
    print("🛰️  SpectraX - Full AWS Cloud Deployment")
    print("=" * 65)

    bucket_name = settings.AWS_S3_BUCKET_NAME
    region = settings.AWS_REGION

    ec2, s3, iam = get_aws_clients()

    # Step 1: S3 outputs/* public access
    configure_s3_public_outputs(s3, bucket_name)

    # Step 2: IAM Role
    profile_name = setup_iam_role(iam, bucket_name)

    # Step 3: Security Group
    sg_id = setup_security_group(ec2)

    # Step 4: Launch EC2
    instance_id, public_ip, public_dns = launch_ec2_instance(
        ec2, sg_id, profile_name, bucket_name, region
    )

    print("\n" + "=" * 65)
    print("🌟 LIVE SHAREABLE DEPLOYMENT DETAILS")
    print("=" * 65)
    print(f"🔗 Public Shareable URL:  http://{public_ip}")
    print(f"🌐 Public AWS DNS:        http://{public_dns}")
    print(f"📦 S3 Public Outputs URL: https://{bucket_name}.s3.{region}.amazonaws.com/outputs/")
    print(f"🖥️  EC2 Instance ID:      {instance_id}")
    print(f"📍 Region:                {region}")
    print("\n⏳ Note: Cloud-init is building the frontend & installing PyTorch packages.")
    print("   The live website will be accessible at the link above within 3-5 minutes!")
    print("=" * 65)


if __name__ == "__main__":
    main()
