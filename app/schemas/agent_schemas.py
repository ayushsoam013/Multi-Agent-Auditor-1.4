from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union


class AgentRequest(BaseModel):
    """
    Standard request payload for all agents.
    Includes both textual and visual data to support multi-modal analysis.
    """

    product_title: Optional[str] = None
    product_specs: Optional[str] = None
    mcat_name: Optional[str] = None
    image_url: Optional[str] = None
    image_path: Optional[str] = None  # Local path for processing
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class BaseAgentResponse(BaseModel):
    """
    Base schema for all agent responses.
    Tracks metadata (time, cost, status) common to all agents.
    """

    agent_name: str
    status: str = "success"  # success, failure
    error_message: Optional[str] = None
    processing_time: float = 0.0
    cost: float = 0.0
    raw_output: Optional[Dict[str, Any]] = None


# Photo Agent Specific Schemas
class VisibilityStatus(BaseModel):
    status: str  # "outlier", "not_outlier", "can't_say"
    reason: str


class PhotoAnalysisResult(BaseModel):
    task_1: Dict[str, str] = Field(..., description="Primary object detection")
    task_2: Dict[str, List[str]] = Field(..., description="OCR text extraction")
    task_3: Dict[str, Dict[str, str]] = Field(..., description="Photo specifications")
    task_4: Dict[str, VisibilityStatus] = Field(
        ..., description="Visibility assessments"
    )


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
    task_2: Dict[str, List[IdentifiedEntity]]
    task_3: Dict[str, str]
    task_4: Dict[str, TaskStatus]


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


# Category Agent Specific Schemas
class CategoryAnalysisResult(BaseModel):
    suggested_category: str
    confidence_score: float
    reasoning: str
    alternative_categories: List[str] = []


class CategoryAgentResponse(BaseAgentResponse):
    analysis: Optional[CategoryAnalysisResult] = None


# RCA Agent Specific Schemas (Used by Master Agent)
class RCAIssue(BaseModel):
    issue_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    evidence: str


class RCAAnalysisResult(BaseModel):
    root_cause_summary: str
    identified_issues: List[RCAIssue] = []
    recommended_verdict: str  # PASS, FAIL, REVIEW
    confidence: float


class RCAAgentResponse(BaseAgentResponse):
    analysis: Optional[RCAAnalysisResult] = None


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
    rca: Optional[RCAAnalysisResult] = None
    cross_validation: CrossValidation = Field(default_factory=CrossValidation)
    final_errors: FinalErrors = Field(default_factory=FinalErrors)
    audit_decision: str = "REVIEW"  # PASS, FAIL, REVIEW
    decision_code: str = "00000"
    seller_recommendation: str = ""
    confidence_score: float = 0.0
    reasons: List[str] = []


# Deployment Agent Specific Schemas
class DeploymentCheck(BaseModel):
    check_name: str
    status: str  # PASS, FAIL
    details: str


class DeploymentAnalysisResult(BaseModel):
    checks: List[DeploymentCheck] = []
    overall_status: str  # READY, NOT_READY
    recommendations: List[str] = []


class DeploymentAgentResponse(BaseAgentResponse):
    analysis: Optional[DeploymentAnalysisResult] = None


class MultiAgentAuditResult(BaseModel):
    """
    Consolidated response containing results from all agents in the pipeline.
    This serves as the final data contract for the Audit API.
    """

    audit_id: str
    photo_agent: Optional[PhotoAgentResponse] = None
    title_agent: Optional[TitleAgentResponse] = None
    specs_agent: Optional[SpecsAgentResponse] = None
    category_agent: Optional[CategoryAgentResponse] = None
    rca_agent: Optional[RCAAgentResponse] = None
    master_agent: Optional[MasterAgentResponse] = None
    total_processing_time: float = 0.0
    total_cost: float = 0.0
