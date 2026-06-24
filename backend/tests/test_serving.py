import requests
import json
import pandas as pd
import numpy as np

# A Train/Serve consistency test script
# This script assumes the backend is running at http://localhost:8000

API_URL = "http://localhost:8000/api/preprocessing"

# These represent known offline predictions from the Phase 6 notebook
# In a real environment, we would load the specific validation rows and their recorded offline probabilities.
# We map known 'claim_id' to their offline probability generated during notebook evaluation.
KNOWN_GROUND_TRUTH = {
    "claim_001_mock": 0.0452,
    "claim_002_mock": 0.8123,
    "claim_003_mock": 0.1154,
    "claim_004_mock": 0.0120,
    "claim_005_mock": 0.4501
}

def run_consistency_test():
    print("Starting Train/Serve Consistency Test...")
    
    success_count = 0
    tolerance = 0.001
    
    for claim_id, offline_prob in KNOWN_GROUND_TRUTH.items():
        try:
            # Send the request to the live API endpoint
            response = requests.post(f"{API_URL}/claims/{claim_id}/predict")
            
            if response.status_code != 200:
                print(f"FAILED: API returned {response.status_code} for {claim_id}")
                continue
                
            data = response.json()
            online_prob = data.get("fraud_probability")
            
            if online_prob is None:
                print(f"FAILED: No probability returned for {claim_id}")
                continue
                
            # Assert online matches offline within tolerance
            diff = abs(online_prob - offline_prob)
            if diff <= tolerance:
                print(f"SUCCESS: {claim_id} | Offline: {offline_prob:.4f} | Online: {online_prob:.4f} | Diff: {diff:.4f}")
                success_count += 1
            else:
                print(f"FAILED MISMATCH: {claim_id} | Offline: {offline_prob:.4f} | Online: {online_prob:.4f} | Diff: {diff:.4f} (>{tolerance})")
                
        except requests.exceptions.ConnectionError:
            print("ERROR: Could not connect to the live API. Please ensure the FastAPI server is running.")
            return
            
    print(f"\nConsistency Test Completed: {success_count}/{len(KNOWN_GROUND_TRUTH)} passed.")
    if success_count == len(KNOWN_GROUND_TRUTH):
        print("All predictions matched offline training results within the acceptable tolerance.")
    else:
        print("WARNING: Some predictions deviated from offline training results (Preprocessing Drift detected).")

if __name__ == "__main__":
    run_consistency_test()
