import pandas as pd
import requests
import time
import os


def test_bulk_audit_resumption():
    print("Starting Bulk Audit Resumption Test...")

    # Paths
    results_path = "misc/audit_results_final.csv"

    # 1. Check current count
    initial_count = 0
    if os.path.exists(results_path):
        df = pd.read_csv(results_path)
        initial_count = len(df)
        print(f"Initial processed items: {initial_count}")
    else:
        print("Results file does not exist. Starting fresh.")

    # 2. Trigger first 2 audits
    print("Auditing 2 items...")
    resp = requests.post(
        "http://localhost:8000/api/v1/bulk-audit/run", params={"limit": 2}
    )
    if resp.status_code != 200:
        print(f"Error triggering audit: {resp.text}")
        return

    # 3. Wait for completion (poll status)
    while True:
        status_resp = requests.get("http://localhost:8000/api/v1/bulk-audit/status")
        status = status_resp.json()
        print(f"Processed items: {status['processed_items']}/{status['total_items']}")
        if status["processed_items"] >= initial_count + 2:
            break
        time.sleep(2)

    print("First 2 items completed.")

    # 4. Trigger next 2 audits
    print("Auditing next 2 items...")
    resp = requests.post(
        "http://localhost:8000/api/v1/bulk-audit/run", params={"limit": 2}
    )
    if resp.status_code != 200:
        print(f"Error triggering audit: {resp.text}")
        return

    # 5. Wait for completion
    while True:
        status_resp = requests.get("http://localhost:8000/api/v1/bulk-audit/status")
        status = status_resp.json()
        print(f"Processed items: {status['processed_items']}/{status['total_items']}")
        if status["processed_items"] >= initial_count + 4:
            break
        time.sleep(2)

    print("Next 2 items completed.")

    # 6. Verify distinct IDs (Logic check)
    df_final = pd.read_csv(results_path)
    processed_ids = df_final["pc_item_id"].tolist()
    unique_ids = set(processed_ids)

    print(f"Total processed: {len(processed_ids)}")
    print(f"Unique processed: {len(unique_ids)}")

    if len(processed_ids) == len(unique_ids):
        print("SUCCESS: No duplicate processing detected. Resumption logic is working.")
    else:
        print("FAILURE: Duplicate processing detected.")


if __name__ == "__main__":
    test_bulk_audit_resumption()
