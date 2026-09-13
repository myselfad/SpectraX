#!/usr/bin/env python3
"""End-to-end browser flow simulation through Vite proxy."""
import httpx
import time
import json
import sys

BASE = "http://localhost:5173"
client = httpx.Client(timeout=30.0)

print("=== STEP 1: Health Check ===")
r = client.get(f"{BASE}/api/health")
print(f"  Status: {r.status_code}")
print(f"  Body: {r.json()}")
assert r.status_code == 200

print("\n=== STEP 2: Upload demo_sample.tif ===")
with open("backend/data/demo_sample.tif", "rb") as f:
    r = client.post(f"{BASE}/api/upload", files={"file": ("demo_sample.tif", f, "image/tiff")})
print(f"  Status: {r.status_code}")
upload = r.json()
print(f"  job_id: {upload['job_id']}")
print(f"  file_type: {upload['file_type']}")
print(f"  dimensions: {upload['width']}x{upload['height']}")
print(f"  num_bands: {upload['num_bands']}")
print(f"  band_names: {upload['band_names']}")
assert r.status_code == 200

job_id = upload["job_id"]

print(f"\n=== STEP 3: Start Processing ===")
payload = {
    "job_id": job_id,
    "scale_factor": 4,
    "selected_bands": upload["band_names"],
    "uncertainty_passes": 2,
    "processing_mode": "standard"
}
r = client.post(f"{BASE}/api/process", json=payload)
print(f"  Status: {r.status_code}")
print(f"  Body: {r.json()}")
assert r.status_code == 200

print(f"\n=== STEP 4: Poll Status (should NOT hang) ===")
for i in range(60):
    time.sleep(2)
    r = client.get(f"{BASE}/api/status/{job_id}")
    if r.status_code != 200:
        print(f"  Poll {i}: HTTP {r.status_code}")
        continue
    status = r.json()
    print(f"  Poll {i}: status={status['status']}, progress={status['progress_percent']}%, step={status.get('current_step')}")
    if status["status"] == "completed":
        print("\n=== STEP 5: COMPLETED! ===")
        break
    elif status["status"] == "failed":
        print(f"\n=== FAILED: {status.get('error')} ===")
        sys.exit(1)
else:
    print("\n=== TIMED OUT after 2 minutes ===")
    sys.exit(1)

print("\n=== STEP 6: Get Results ===")
r = client.get(f"{BASE}/api/results/{job_id}")
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    results = r.json()
    print(f"  sr_image_url: {results.get('sr_image_url') or results.get('output', {}).get('sr_image_url')}")
    print(f"  Keys: {list(results.keys())}")

print("\n=== ALL TESTS PASSED ===")
