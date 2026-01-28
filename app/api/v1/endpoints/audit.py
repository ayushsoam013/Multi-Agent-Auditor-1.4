from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import Optional, List
import os
import shutil
import uuid
from app.schemas.agent_schemas import AgentRequest, MultiAgentAuditResult
from app.services.multi_agent_orchestrator import orchestrator
from app.services.audit_persistence import audit_persistence
from app.core.config import settings
import json
from fastapi import Body

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


@router.post("/save")
async def save_audit_session(
    product_title: str = Form(...),
    product_specs: str = Form(...),
    mcat_name: str = Form(...),
    audit_result: str = Form(...),  # JSON string of MultiAgentAuditResult
    file: UploadFile = File(...),
):
    """
    Saves the current audit session (inputs, image, and result).
    Returns a session ID.
    """
    try:
        # Parse audit result JSON
        audit_result_dict = json.loads(audit_result)
        
        # Prepare data package
        session_data = {
            "product_title": product_title,
            "product_specs": product_specs,
            "mcat_name": mcat_name,
            "audit_result": audit_result_dict
        }
        
        # Save using persistence service
        session_id = audit_persistence.save_audit_session(session_data, file)
        
        return {"session_id": session_id, "message": "Session saved successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save session: {str(e)}")


@router.get("/session/{session_id}")
async def get_audit_session(session_id: str):
    """
    Retrieves a saved audit session by ID.
    """
    try:
        data = audit_persistence.get_audit_session(session_id)
        if not data:
            raise HTTPException(status_code=404, detail="Session not found")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve session: {str(e)}")
