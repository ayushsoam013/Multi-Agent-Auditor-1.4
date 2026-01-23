# Simplified Bulk Audit Plan

This plan outlines a direct, CSV-based approach for auditing multiple products. It ensures data integrity by keeping the input separate from the results and supports resumption.

## 1. Core Workflow

1.  **Input**: Read product information from `misc/input_data.csv`.
2.  **Resumption Check**: Load `misc/audit_results.csv` (if it exists) to identify which `pc_item_id` values have already been audited.
3.  **Processing**: Loop through records in `input_data.csv` that are NOT in `audit_results.csv`, up to an optional limit. **Processing must be STRICTLY SEQUENTIAL (one row at a time) to avoid overwhelming the backend and API rate limits.**
4.  **Execution**: For each record, execute the Multi-Agent Audit. Use a library like `tqdm` to provide a progress bar in the terminal.
5.  **Persistence**: Append the audit results to `misc/audit_results.csv` immediately after each audit.
6.  **Rate Limiting**: Introduce a small delay (1-2 seconds) between sequential audits to ensure API stability.
7.  **Monitoring**: The Streamlit dashboard reads the results CSV to display live progress and aggregate metrics.

## 2. CSV Data Structures

### Input (`misc/input_data.csv`)
*   `pc_item_id`: Unique identifier for the product.
*   `product_title`: Name of the product (or `Product Name` in actual CSV).
*   `product_specs`: Technical specifications (or `Specifications` in actual CSV).
*   `image_url`: Link to the product image (or `img_url` in actual CSV).

### Results (`misc/audit_results.csv`)
*   `pc_item_id`: Unique identifier (links to input).
*   `status`: `completed` or `failed`.
*   `cost`: Individual cost of the audit (USD).
*   `latency`: API response latency.
*   `total_time_taken`: Total execution time for the record (seconds).
*   `response_json`: Full JSON response from the multi-agent system.
*   `error_message`: Details if the audit failed.

## 3. Metrics Tracking

Aggregate metrics will be calculated by scanning `misc/audit_results.csv`:
*   **Total Cost**: Sum of `cost`.
*   **Success Rate**: Percentage of records with `status=completed`.
*   **Average Latency**: Average of the `latency` column.
*   **Progress**: Count of unique `pc_item_id` in results vs. count in input.

## 4. Implementation Steps

### Backend (FastAPI)
1.  **Endpoint**: `POST /api/v1/bulk-audit/run`
2.  **Parameters**: `limit: int` (Optional, e.g., run only 5 rows).
3.  **Logic**:
    *   Load all IDs from `misc/audit_results.csv`.
    *   Read `misc/input_data.csv` and filter out already processed IDs.
    *   Apply `limit` if provided.
    *   **Strictly Sequential Execution**:
        *   Initialize `tqdm` progress bar for terminal visibility.
        *   For each record:
            *   Output progress to terminal: `Row X/Y | pc_item_id: [pc_item_id] | [Progress]%`.
            *   Trigger `MultiAgentOrchestrator`.
            *   Capture cost, latency, time, and full response.
            *   Append a new row to `misc/audit_results.csv`.
            *   **Delay**: Introduce a 1-2 second pause before the next iteration to prevent rate limiting.

### Frontend (Streamlit)
1.  **Dashboard**: Add a "Bulk Audit" page.
2.  **Display**:
    *   Show current progress and metrics using `misc/audit_results.csv`.
    *   Provide a "Start Bulk Audit" button that sends the `limit` to the backend.

## 5. Error Handling & Resumption
*   **Resume**: The system automatically skips any `pc_item_id` found in `misc/audit_results.csv`.
*   **Clean Slate**: To restart from scratch, simply delete or rename `misc/audit_results.csv`.
