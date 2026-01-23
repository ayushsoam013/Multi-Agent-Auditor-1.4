from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import Optional, List
import os
import shutil
import uuid
from app.schemas.agent_schemas import AgentRequest, MultiAgentAuditResult
from app.services.multi_agent_orchestrator import orchestrator
from app.core.config import settings

router = APIRouter()

TEMP_UPLOAD_DIR = "temp_uploads"
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)


@router.post("/multi-agent", response_model=MultiAgentAuditResult)
async def perform_multi_agent_audit(
    product_title: str = Form(...),
    product_specs: str = Form(...),
    mcat_name: str = Form(None),
    file: UploadFile = File(...),
):
    """
    Performs a multi-agent audit on a product photo, title, and specifications.
    Processes specialized agents in parallel and aggregates with a Master Agent.

    - **mcat_name**: Category Name provided by the user (optional).
    """
    try:
        # Save uploaded file temporarily
        file_ext = os.path.splitext(file.filename)[1]
        temp_filename = f"{uuid.uuid4()}{file_ext}"
        temp_path = os.path.join(TEMP_UPLOAD_DIR, temp_filename)

        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Create request object
        request = AgentRequest(
            product_title=product_title,
            product_specs=product_specs,
            mcat_name=mcat_name,
            image_path=temp_path,
        )

        # Run orchestrator
        result = await orchestrator.run_audit(request)

        # Cleanup temp file (could be moved to background task)
        # os.remove(temp_path)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
