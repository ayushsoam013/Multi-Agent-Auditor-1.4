from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union

class AgentRequest(BaseModel):
    product_title: Optional[str] = None
    product_specs: Optional[str] = None
    mcat_name: Optional[str] = None
    image_url: Optional[str] = None
    image_path: Optional[str] = None # Local path for processing
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)

class BaseAgentResponse(BaseModel):
    agent_name: str
    status: str = "success" # success, failure
    error_message: Optional[str] = None
    processing_time: float = 0.0
    raw_output: Optional[Dict[str, Any]] = None

# Photo Agent Specific Schemas
class VisibilityStatus(BaseModel):
    status: str # "outlier", "not_outlier", "can't_say"
    reason: str

class PhotoAnalysisResult(BaseModel):
    task_1: Dict[str, str] = Field(..., description="Primary object detection")
    task_2: Dict[str, List[str]] = Field(..., description="OCR text extraction")
    task_3: Dict[str, Dict[str, str]] = Field(..., description="Photo specifications")
    task_4: Dict[str, VisibilityStatus] = Field(..., description="Visibility assessments")

class PhotoAgentResponse(BaseAgentResponse):
    analysis: Optional[PhotoAnalysisResult] = None

# Title Agent Specific Schemas
class TaskStatus(BaseModel):
    status: str = ""
    reason: str = ""

class IdentifiedEntity(BaseModel):
    entity: str
    source: str
    why_popular: str

class TitleAnalysisResult(BaseModel):
    task_1: Dict[str, TaskStatus]
    task_2: Dict[str, TaskStatus]
    task_3: Dict[str, List[IdentifiedEntity]]
    task_4: Dict[str, str]
    task_5: Dict[str, TaskStatus]
    task_6: Dict[str, TaskStatus]
    task_7: Dict[str, TaskStatus]

class TitleAgentResponse(BaseAgentResponse):
    analysis: Optional[TitleAnalysisResult] = None

# Specs Agent Specific Schemas
class SpecsAnalysisResult(BaseModel):
    spell_errors: List[str] = []
    duplicate_specs: List[str] = []
    contradictions: List[str] = []
    extracted_specs: Dict[str, str] = {}

class SpecsAgentResponse(BaseAgentResponse):
    analysis: Optional[SpecsAnalysisResult] = None

# Master Agent Specific Schemas
class CrossValidation(BaseModel):
    photo_title_contradiction: bool = False
    photo_specs_contradiction: bool = False
    title_specs_contradiction: bool = False
    search_query_contradiction: bool = False

class FinalErrors(BaseModel):
    photo_quality_error: bool = False
    title_quality_error: bool = False
    title_contradiction_error: bool = False
    specs_quality_error: bool = False
    specs_contradiction_error: bool = False
    photo_category_error: bool = False
    title_category_error: bool = False
    category_contradiction_error: bool = False

class MasterAgentResponse(BaseAgentResponse):
    product_search_query: str = ""
    cross_validation: CrossValidation = Field(default_factory=CrossValidation)
    final_errors: FinalErrors = Field(default_factory=FinalErrors)
    audit_decision: str = "REVIEW" # PASS, FAIL, REVIEW
    confidence_score: float = 0.0
    reasons: List[str] = []

class MultiAgentAuditResult(BaseModel):
    audit_id: str
    photo_agent: Optional[PhotoAgentResponse] = None
    title_agent: Optional[TitleAgentResponse] = None
    specs_agent: Optional[SpecsAgentResponse] = None
    master_agent: Optional[MasterAgentResponse] = None
    total_processing_time: float = 0.0
