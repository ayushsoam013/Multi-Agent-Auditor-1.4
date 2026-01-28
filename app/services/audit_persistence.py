import os
import json
import uuid
import shutil
from fastapi import UploadFile
from typing import Dict, Any

SAVED_AUDITS_DIR = "saved_audits"
IMAGES_DIR = os.path.join(SAVED_AUDITS_DIR, "images")
DATA_DIR = os.path.join(SAVED_AUDITS_DIR, "data")

# Ensure directories exist
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

class AuditPersistenceService:
    def save_audit_session(self, data: Dict[str, Any], image_file: UploadFile) -> str:
        """
        Saves the audit session data and image.
        Returns the session_id (UUID).
        """
        session_id = str(uuid.uuid4())
        
        # Save Image
        file_ext = os.path.splitext(image_file.filename)[1]
        if not file_ext:
            file_ext = ".jpg" # Default fallback
            
        image_filename = f"{session_id}{file_ext}"
        image_path = os.path.join(IMAGES_DIR, image_filename)
        
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image_file.file, buffer)
            
        # Update data with relative image path for retrieval
        # We will serve images via /static/saved_audits/images/{filename}
        data["image_url"] = f"/static/saved_audits/images/{image_filename}"
        data["session_id"] = session_id
        
        # Save JSON Data
        json_path = os.path.join(DATA_DIR, f"{session_id}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
        return session_id

    def get_audit_session(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieves the audit session data by ID.
        """
        json_path = os.path.join(DATA_DIR, f"{session_id}.json")
        
        if not os.path.exists(json_path):
            return None
            
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        return data

audit_persistence = AuditPersistenceService()
