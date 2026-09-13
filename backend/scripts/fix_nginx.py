#!/usr/bin/env python3
import sys
from pathlib import Path
import time

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
import boto3

ssm = boto3.client(
    "ssm",
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)

nginx_text = """server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 100M;

    location / {
        root /var/www/spectrax/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
"""

import base64
b64_content = base64.b64encode(nginx_text.encode("utf-8")).decode("ascii")

shell_commands = [
    f"python3 -c \"import base64; open('/etc/nginx/sites-available/spectrax', 'w').write(base64.b64decode('{b64_content}').decode('utf-8'))\"",
    "rm -f /etc/nginx/sites-enabled/default",
    "ln -sf /etc/nginx/sites-available/spectrax /etc/nginx/sites-enabled/spectrax",
    "nginx -t",
    "systemctl restart nginx",
    "systemctl is-active nginx",
    "curl -s http://127.0.0.1/api/health",
]

res = ssm.send_command(
    InstanceIds=["i-08d66878c7f4ea578"],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": shell_commands},
)
cmd_id = res["Command"]["CommandId"]
print("SSM Command Sent:", cmd_id)

for _ in range(10):
    time.sleep(2)
    out = ssm.get_command_invocation(
        CommandId=cmd_id, InstanceId="i-08d66878c7f4ea578"
    )
    if out["Status"] in ("Success", "Failed"):
        print("Status:", out["Status"])
        print("Standard Output:\n", out["StandardOutputContent"])
        if out["StandardErrorContent"]:
            print("Standard Error:\n", out["StandardErrorContent"])
        break
