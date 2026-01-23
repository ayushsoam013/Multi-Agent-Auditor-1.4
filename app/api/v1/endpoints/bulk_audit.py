from fastapi import APIRouter, BackgroundTasks, Query, HTTPException
from typing import Optional
from app.services.bulk_audit_service import bulk_audit_service
from app.schemas.agent_schemas import BulkAuditSummary

router = APIRouter()


@router.post("/run")
async def run_bulk_audit(
    background_tasks: BackgroundTasks,
    limit: Optional[int] = Query(
        None, description="Limit the number of products to audit"
    ),
):
    """
    Triggers a bulk audit process in the background.
    """
    if bulk_audit_service.is_running:
        raise HTTPException(status_code=409, detail="Bulk audit is already running")

    background_tasks.add_task(bulk_audit_service.run_bulk_audit, limit)
    return {"message": "Bulk audit started in background", "limit": limit}


@router.get("/status", response_model=BulkAuditSummary)
async def get_bulk_audit_status():
    """
    Returns the current progress and metrics of the bulk audit.
    Calculated based on misc/audit_results.csv.
    """
    return bulk_audit_service.get_summary()
