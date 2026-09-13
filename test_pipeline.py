import httpx
import time
import json
import sys

client = httpx.Client(timeout=None)

def run_test(scale):
    print(f"\n--- TESTING {scale}x PIPELINE ---")
    
    print("1. Health check")
    res = client.get("http://localhost:8000/api/health")
    if res.status_code != 200:
        print("FAIL: health check")
        return False
    print("Health:", res.json())

    print("2. Upload file")
    with open("backend/data/demo_sample.tif", "rb") as f:
        res = client.post("http://localhost:8000/api/upload", files={"file": f})
    if res.status_code != 200:
        print("FAIL: Upload")
        return False
    upload_data = res.json()
    job_id = upload_data["job_id"]
    print("Job ID:", job_id, "Width:", upload_data['width'], "Bands:", upload_data['num_bands'])

    print(f"3. Process ({scale}x)")
    req = {
        "job_id": job_id,
        "scale_factor": scale,
        "selected_bands": ["red", "green", "blue", "nir"],
        "uncertainty_passes": 2, # Use 2 for fast testing
        "processing_mode": "standard"
    }
    res = client.post("http://localhost:8000/api/process", json=req)
    if res.status_code != 200:
        print("FAIL: Process start")
        return False
    
    print("4. Polling status...")
    while True:
        time.sleep(2)
        res = client.get(f"http://localhost:8000/api/status/{job_id}")
        if res.status_code != 200:
            print("FAIL: Status check")
            return False
        status_data = res.json()
        status = status_data.get("status")
        prog = status_data.get("progress_percent")
        step = status_data.get("current_step")
        print(f"Status: {status} - {prog}% - Step: {step}")
        if status in ["completed", "failed"]:
            if status == "failed":
                print("FAIL: Pipeline failed:", status_data.get("error"))
                return False
            break

    print("5. Results")
    res = client.get(f"http://localhost:8000/api/results/{job_id}")
    if res.status_code != 200:
        print("FAIL: Results")
        return False
    
    results = res.json()
    print("Output Dimensions:", results['output']['width'], "x", results['output']['height'])
    
    print("6. Testing Downloads")
    for file_type in ['sr_image', 'uncertainty_map', 'reliability_map']:
        dl_res = client.get(f"http://localhost:8000/api/export/{job_id}/{file_type}")
        if dl_res.status_code != 200:
            print(f"FAIL: Download {file_type} failed")
            return False
        print(f"Downloaded {file_type} successfully ({len(dl_res.content)} bytes)")
        
    print(f"--- {scale}x PIPELINE SUCCESS ---")
    return True

if __name__ == "__main__":
    s1 = run_test(2)
    s2 = run_test(4)
    if not (s1 and s2):
        sys.exit(1)
