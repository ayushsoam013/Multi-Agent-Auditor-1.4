import os
import asyncio
import pandas as pd
import aiohttp
import aiofiles
import time
import json
import logging
import re
from typing import List, Optional, Dict, Any
from tqdm import tqdm

from app.core.config import settings
from app.schemas.agent_schemas import (
    AgentRequest,
    MultiAgentAuditResult,
    BulkAuditSummary,
)
from app.services.multi_agent_orchestrator import orchestrator

logger = logging.getLogger(__name__)


class BulkAuditService:
    def __init__(self):
        self.input_path = settings.BULK_AUDIT_INPUT_PATH
        self.results_path = settings.BULK_AUDIT_RESULTS_PATH
        self.temp_dir = settings.BULK_AUDIT_TEMP_DIR
        os.makedirs(self.temp_dir, exist_ok=True)
        self._is_running = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    async def run_bulk_audit(self, limit: Optional[int] = None) -> None:
        if self._is_running:
            logger.warning("Bulk audit is already running.")
            return

        self._is_running = True
        try:
            # 1. Load input
            if not os.path.exists(self.input_path):
                logger.error(f"Input file not found: {self.input_path}")
                return

            df_input = pd.read_csv(self.input_path)

            # 2. Load results for resumption
            processed_ids = set()
            if os.path.exists(self.results_path):
                try:
                    df_results = pd.read_csv(self.results_path)
                    processed_ids = set(df_results["pc_item_id"].astype(str).tolist())
                except Exception as e:
                    logger.error(f"Error reading results CSV: {e}")

            # 3. Filter pending
            is_processed = df_input["pc_item_id"].astype(str).isin(list(processed_ids))
            df_pending = df_input[~is_processed]

            if limit:
                df_pending = df_pending.head(limit)

            total_to_process = len(df_pending)
            if total_to_process == 0:
                logger.info("No pending items to process.")
                return

            logger.info(f"Starting bulk audit for {total_to_process} items.")

            # 4. Sequential Processing
            for _, row in tqdm(
                df_pending.iterrows(), total=total_to_process, desc="Bulk Auditing"
            ):
                pc_item_id = str(row["pc_item_id"])
                # Sanitize pc_item_id to prevent path traversal
                pc_item_id = re.sub(r"[^a-zA-Z0-9_\-]", "", pc_item_id)

                product_title = row.get("Product Name", row.get("product_title", ""))
                img_url = str(row.get("img_url", row.get("image_url", "")))
                product_specs = row.get(
                    "Specifications", row.get("product_specs", "[]")
                )
                mcat_name = row.get("Category Name", row.get("mcat_name", ""))
                reference_val = row.get("reference_outlier_api_raw_response", "")

                # Fix for LSP error: Ensure we are checking for null correctly
                is_mcat_na = (
                    pd.isna(mcat_name)
                    if not isinstance(mcat_name, (pd.DataFrame, pd.Series))
                    else mcat_name.isna().any()
                )
                is_ref_na = (
                    pd.isna(reference_val)
                    if not isinstance(reference_val, (pd.DataFrame, pd.Series))
                    else reference_val.isna().any()
                )

                reference_outlier_api_raw_response = (
                    str(reference_val) if not is_ref_na else ""
                )

                start_time = time.time()
                try:
                    # Download image
                    image_path = await self._download_image(img_url, pc_item_id)

                    # Run Audit
                    request = AgentRequest(
                        product_title=str(product_title),
                        product_specs=str(product_specs),
                        mcat_name=str(mcat_name) if not is_mcat_na else None,
                        image_path=image_path,
                    )

                    result: MultiAgentAuditResult = await orchestrator.run_audit(
                        request
                    )

                    # Save result
                    self._append_result(
                        pc_item_id=pc_item_id,
                        status="completed",
                        result=result,
                        start_time=start_time,
                        reference_outlier_api_raw_response=str(
                            reference_outlier_api_raw_response
                        ),
                    )

                    # Cleanup
                    if image_path and os.path.exists(image_path):
                        os.remove(image_path)

                except Exception as e:
                    logger.error(f"Failed to process {pc_item_id}: {str(e)}")
                    self._append_result(
                        pc_item_id=pc_item_id,
                        status="failed",
                        result=None,
                        start_time=start_time,
                        error_message=str(e),
                        reference_outlier_api_raw_response=str(
                            reference_outlier_api_raw_response
                        ),
                    )

                # Rate limiting delay removed
                # await asyncio.sleep(1.5)
        finally:
            self._is_running = False

    async def _download_image(self, url: str, item_id: str) -> Optional[str]:
        if not url or not isinstance(url, str) or not url.startswith("http"):
            return None
        try:
            # Timeout removed (total=None means no timeout)
            timeout = aiohttp.ClientTimeout(total=None)
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout) as response:
                    if response.status == 200:
                        file_ext = os.path.splitext(url.split("?")[0])[-1]
                        if not file_ext or len(file_ext) > 5:
                            file_ext = ".jpg"
                        file_path = os.path.join(self.temp_dir, f"{item_id}{file_ext}")
                        async with aiofiles.open(file_path, mode="wb") as f:
                            await f.write(await response.read())
                        return file_path
                    else:
                        logger.warning(
                            f"Failed to download {url}: Status {response.status}"
                        )
        except Exception as e:
            logger.error(f"Download failed for {url}: {e}")
        return None

    def _append_result(
        self,
        pc_item_id: str,
        status: str,
        result: Optional[MultiAgentAuditResult],
        start_time: float,
        error_message: Optional[str] = None,
        reference_outlier_api_raw_response: Optional[str] = None,
    ) -> None:
        end_time = time.time()
        total_time = end_time - start_time

        data = {
            "pc_item_id": pc_item_id,
            "status": status,
            "reference_outlier_api_raw_response": reference_outlier_api_raw_response,
            "photo_agent_response_json": json.dumps(result.photo_agent.model_dump())
            if result and result.photo_agent
            else None,
            "photo_agent_latency": result.photo_agent.processing_time
            if result and result.photo_agent
            else 0.0,
            "photo_agent_cost": result.photo_agent.cost
            if result and result.photo_agent
            else 0.0,
            "textual_agent_response_json": json.dumps(result.textual_agent.model_dump())
            if result and result.textual_agent
            else None,
            "textual_agent_latency": result.textual_agent.processing_time
            if result and result.textual_agent
            else 0.0,
            "textual_agent_cost": result.textual_agent.cost
            if result and result.textual_agent
            else 0.0,
            "rca_agent_response_json": json.dumps(result.rca_agent.model_dump())
            if result and result.rca_agent
            else None,
            "rca_agent_latency": result.rca_agent.processing_time
            if result and result.rca_agent
            else 0.0,
            "rca_agent_cost": result.rca_agent.cost
            if result and result.rca_agent
            else 0.0,
            "category_agent_response_json": json.dumps(
                result.category_agent.model_dump()
            )
            if result and result.category_agent
            else None,
            "category_agent_latency": result.category_agent.processing_time
            if result and result.category_agent
            else 0.0,
            "category_agent_cost": result.category_agent.cost
            if result and result.category_agent
            else 0.0,
            "master_agent_response_json": json.dumps(result.master_agent.model_dump())
            if result and result.master_agent
            else None,
            "master_agent_latency": result.master_agent.processing_time
            if result and result.master_agent
            else 0.0,
            "master_agent_cost": result.master_agent.cost
            if result and result.master_agent
            else 0.0,
            "total_latency": result.total_processing_time if result else 0.0,
            "total_cost": result.total_cost if result else 0.0,
            "total_time_taken": total_time,
            "error_message": error_message,
        }

        file_exists = os.path.exists(self.results_path)
        df = pd.DataFrame([data])
        # Use a lock or just rely on atomic-ish append for single worker
        df.to_csv(self.results_path, mode="a", index=False, header=not file_exists)

    def get_summary(self) -> BulkAuditSummary:
        if not os.path.exists(self.results_path):
            # Try to get total items from input
            total_items = 0
            if os.path.exists(self.input_path):
                total_items = len(pd.read_csv(self.input_path))

            return BulkAuditSummary(
                total_items=total_items,
                processed_items=0,
                completed_items=0,
                failed_items=0,
                total_cost=0.0,
                average_latency=0.0,
                success_rate=0.0,
                progress_percentage=0.0,
            )

        df_results = pd.read_csv(self.results_path)
        total_items = 0
        if os.path.exists(self.input_path):
            total_items = len(pd.read_csv(self.input_path))
        else:
            total_items = len(df_results)

        processed_items = len(df_results)
        completed_items = int(len(df_results[df_results["status"] == "completed"]))
        failed_items = int(len(df_results[df_results["status"] == "failed"]))
        total_cost = float(df_results["total_cost"].sum())
        average_latency = (
            float(df_results["total_latency"].mean()) if not df_results.empty else 0.0
        )
        success_rate = (
            float(completed_items / processed_items * 100)
            if processed_items > 0
            else 0.0
        )
        progress_percentage = (
            float(processed_items / total_items * 100) if total_items > 0 else 0.0
        )

        return BulkAuditSummary(
            total_items=total_items,
            processed_items=processed_items,
            completed_items=completed_items,
            failed_items=failed_items,
            total_cost=total_cost,
            average_latency=average_latency,
            success_rate=success_rate,
            progress_percentage=progress_percentage,
        )


bulk_audit_service = BulkAuditService()
