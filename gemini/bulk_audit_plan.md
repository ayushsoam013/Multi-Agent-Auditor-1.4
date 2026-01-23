# Detailed Plan for Bulk Auditing (10,000 Products)

## Executive Summary
Performing a deep multi-agent audit on 10,000 products requires a robust, asynchronous architecture to handle long-running processes, potential API rate limits (Gemini/LiteLLM), and system resilience. This plan proposes a **Batch Processing System** backed by a lightweight SQLite database to manage state, ensure no data loss, and allow for resumable audits.

## 1. Architecture Overview

The system will transition from a synchronous "request-response" model to an asynchronous "job-queue" model for bulk operations.

### Workflow:
1.  **Client** uploads a CSV/JSON file containing product details (Title, Specs, Image URLs) via a new API endpoint.
2.  **Server** parses the file, creates a `Batch` record, and inserts 10,000 `AuditTask` records into a local SQLite database.
3.  **Server** returns a `batch_id` immediately.
4.  **Background Worker** (running in a separate thread/process) polls the database for `pending` tasks.
5.  **Worker** processes tasks with concurrency control (e.g., semaphore) to manage API rate limits.
6.  **Results** are saved back to the SQLite database.
7.  **Client** polls for progress or downloads the final report via a retrieval endpoint.

## 2. Data Persistence (SQLite)

We will introduce a local `audit.db` (SQLite) to track the state of every single audit. This ensures that if the server crashes after processing 5,000 items, we can resume exactly where we left off.

### Schema Design

**Table: `batches`**
- `id` (UUID, PK): Unique batch identifier.
- `filename` (Text): Name of the uploaded file.
- `status` (Text): `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`.
- `created_at` (Datetime)
- `total_items` (Integer): Total records (e.g., 10,000).
- `processed_count` (Integer): Live counter of finished tasks.

**Table: `audit_tasks`**
- `id` (Integer, PK, Auto-increment)
- `batch_id` (UUID, FK): Link to parent batch.
- `input_data` (JSON): Stores `{product_title, product_specs, image_url, ...}`.
- `status` (Text): `PENDING`, `IN_PROGRESS`, `SUCCESS`, `FAILED`.
- `result` (JSON): Stores the full `MultiAgentAuditResult` or error details.
- `attempts` (Integer): To track retries.
- `updated_at` (Datetime)

## 3. API Design Changes

We need to add a new router `app/api/v1/endpoints/bulk_audit.py` with the following endpoints:

### 1. Upload Batch
`POST /api/v1/bulk-audit/upload`
- **Input**: CSV or JSON file.
- **Action**: Parses file, populates DB, starts background worker.
- **Output**: `{"batch_id": "...", "message": "Batch accepted. 10,000 tasks queued."}`

### 2. Check Progress
`GET /api/v1/bulk-audit/{batch_id}/status`
- **Output**:
  ```json
  {
    "batch_id": "...",
    "status": "PROCESSING",
    "progress": "45.2%",
    "processed": 4520,
    "total": 10000,
    "failed": 12
  }
  ```

### 3. Download Results
`GET /api/v1/bulk-audit/{batch_id}/results`
- **Query Param**: `format=json|csv`
- **Action**: Streaming response of all completed audits for this batch.

## 4. Implementation Details

### A. Background Worker Logic
We will use Python's `asyncio` with a `Semaphore` to control concurrency.

```python
MAX_CONCURRENT_AUDITS = 5  # Adjust based on LLM rate limits

async def process_batch(batch_id: str):
    tasks = db.get_pending_tasks(batch_id)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_AUDITS)
    
    async def worker(task):
        async with semaphore:
            try:
                # 1. Download image from URL (if needed)
                # 2. Call orchestrator.run_audit(request)
                # 3. Update task status to SUCCESS in DB
            except Exception as e:
                # Update task status to FAILED in DB
                
    await asyncio.gather(*[worker(task) for task in tasks])
```

### B. Handling Images
For 10,000 items, we cannot upload images directly.
- **Requirement**: The input CSV must contain `image_url`.
- **Logic**: The worker must download the image to a temporary path, pass it to the `PhotoAgent`, and delete it immediately after processing to save disk space.

### C. Rate Limiting & Retries
- **Rate Limits**: If the LLM API returns a 429 (Too Many Requests), the worker should implement an exponential backoff strategy (sleep 2s, 4s, 8s...).
- **Retries**: If a task fails due to a transient network error, increment `attempts` and reset status to `PENDING` (up to 3 times).

## 5. Phase-by-Phase Rollout Plan

### Phase 1: Foundation (Days 1-2)
- Set up `sqlite3` connection and schema creation script.
- Create `bulk_audit.py` router skeleton.
- Implement the "Upload" endpoint to just parse CSV and save to DB (no processing yet).

### Phase 2: The Worker (Days 3-4)
- Implement the `process_batch` background function.
- Integrate `MultiAgentOrchestrator`.
- Add image downloading utility.
- Test with a small batch (10 items).

### Phase 3: Reliability (Day 5)
- Add Global Exception Handlers.
- Implement Retry logic.
- Add "Pause/Resume" functionality (optional but recommended).

## 6. Required Dependencies
You may need to add these to `requirements.txt`:
- `aiohttp`: For efficient async image downloading.
- `aiosqlite`: For async SQLite interactions (prevents blocking the main API thread).
- `pandas` (optional): For robust CSV parsing.

## 7. Configuration
Add these to `.env`:
```
MAX_CONCURRENT_AUDITS=5
SQLITE_DB_PATH=./audit.db
```
