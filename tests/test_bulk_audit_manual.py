import asyncio
import os
import sys
import pandas as pd

# Add project root to path
sys.path.append(os.getcwd())

from app.services.bulk_audit_service import bulk_audit_service
from app.core.config import settings


async def main():
    print("=== Bulk Audit Integration Test ===")
    print(f"Using Input: {bulk_audit_service.input_path}")
    print(f"Using Results: {bulk_audit_service.results_path}")

    # Check if input file exists
    if not os.path.exists(bulk_audit_service.input_path):
        print(f"Error: {bulk_audit_service.input_path} not found.")
        return

    # To avoid messing up existing results if any, we can backup or just run
    # For testing purposes, we'll just run and see if it appends.

    limit = 2
    print(f"\nProcessing {limit} samples...")
    await bulk_audit_service.run_bulk_audit(limit=limit)

    # Check results
    if os.path.exists(bulk_audit_service.results_path):
        df = pd.read_csv(bulk_audit_service.results_path)
        print("\n--- Summary of Latest Runs ---")
        print(
            df.tail(limit)[["pc_item_id", "status", "total_cost", "total_time_taken"]]
        )

        summary = bulk_audit_service.get_summary()
        print("\n--- Overall Summary ---")
        print(f"Total Items: {summary.total_items}")
        print(f"Processed: {summary.processed_items}")
        print(f"Success Rate: {summary.success_rate:.2f}%")
        print(f"Total Cost: ${summary.total_cost:.6f}")
    else:
        print("\nError: audit_results.csv was not created.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted.")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
