import json
import logging
from typing import Dict, Any, Optional, List
from app.services.agents.base_agent import BaseAgent
from app.schemas.agent_schemas import (
    AgentRequest, 
    MasterAgentResponse, 
    PhotoAgentResponse, 
    TitleAgentResponse, 
    SpecsAgentResponse,
    CrossValidation,
    FinalErrors
)
from app.core.decision_grid import decision_grid_loader

logger = logging.getLogger(__name__)

class MasterAgent(BaseAgent):
    def __init__(self, model_name: Optional[str] = None):
        super().__init__(
            agent_name="MasterAgent", 
            model_name=model_name or "gemini-1.5-flash",
            response_class=MasterAgentResponse
        )

    async def _process_logic(self, request: AgentRequest) -> Dict[str, Any]:
        """
        Master Agent logic:
        1. Receive aggregated agent results (sent via context in request)
        2. Perform cross-validation analysis
        3. Use DecisionGrid for rule-based matching
        4. Generate final search query and summary
        """
        agent_results = request.context.get("agent_results", {})
        photo_res: Optional[PhotoAgentResponse] = agent_results.get("photo")
        title_res: Optional[TitleAgentResponse] = agent_results.get("title")
        specs_res: Optional[SpecsAgentResponse] = agent_results.get("specs")

        # 1. Cross-Validation Analytics
        cross_val = self._perform_cross_validation(photo_res, title_res, specs_res)
        
        # 2. Extract Facts for Decision Grid
        facts = self._extract_facts(photo_res, title_res, specs_res, cross_val)
        
        # 3. Apply Decision Grid Rules
        decision = decision_grid_loader.get_decision(facts)
        
        # 4. Generate Final Response using LLM for summary and search query
        prompt = self._get_master_prompt(request, photo_res, title_res, specs_res, cross_val, decision)
        
        response = await self.gen_service.chat_with_usage(
            messages=[{"role": "user", "content": prompt}],
            config={"response_mime_type": "application/json"}
        )
        
        raw_text = response.get("content", "{}")
        try:
            result = json.loads(raw_text)
            # Merge rule-based decision into LLM generated result
            result["audit_decision"] = decision["action"]
            result["confidence_score"] = decision.get("confidence", 0.5)
            result["cross_validation"] = cross_val.model_dump()
            return result
        except Exception as e:
            logger.error(f"Failed to parse MasterAgent response: {raw_text}")
            raise e

    def _perform_cross_validation(self, photo, title, specs) -> CrossValidation:
        cv = CrossValidation()
        # With the new TitleAgent requirements, Task 5 and Task 6 handle contradictions
        if title and title.status == "success" and title.analysis:
            task_5 = title.analysis.task_5
            
            def get_status(task_key):
                val = task_5.get(task_key)
                if not val: return None
                return val.status if hasattr(val, "status") else val.get("status")

            if get_status("photo_title") == "outlier":
                cv.photo_title_contradiction = True
            if get_status("photo_specs") == "outlier":
                cv.photo_specs_contradiction = True
            if get_status("title_specs") == "outlier":
                cv.title_specs_contradiction = True
            if get_status("query_internal") == "outlier":
                cv.search_query_contradiction = True
            
        return cv

    def _extract_facts(self, photo, title, specs, cv) -> Dict[str, Any]:
        facts = {
            "photo_quality_error": False,
            "title_quality_error": False,
            "title_contradiction_error": False,
            "specs_quality_error": False,
            "specs_contradiction_error": False,
        }
        
        if photo and photo.status == "success" and photo.analysis:
            # Check Task 4 for outliers
            for task, details in photo.analysis.task_4.items():
                if getattr(details, "status", None) == "outlier" or (isinstance(details, dict) and details.get("status") == "outlier"):
                    facts["photo_quality_error"] = True
                    break
        
        if title and title.status == "success" and title.analysis:
            # Check Task 1 for title quality/errors
            task_1 = title.analysis.task_1
            for v in task_1.values():
                status = v.status if hasattr(v, "status") else v.get("status")
                if status == "outlier":
                    facts["title_quality_error"] = True
                    break
                
            # Task 5 contains cross-contradictions
            if cv.photo_title_contradiction or cv.title_specs_contradiction:
                facts["title_contradiction_error"] = True
                
        return facts

    def _get_master_prompt(self, request, photo, title, specs, cross_val, decision) -> str:
        return f"""
You are the Master Auditor Agent. You have received reports from specialized agents:
- Photo Agent Analysis: {json.dumps(photo.model_dump() if photo else {{}})}
- Title Agent Analysis: {json.dumps(title.model_dump() if title else {{}})}
- Specs Agent Analysis: {json.dumps(specs.model_dump() if specs else {{}})}

Current Rule-Based Decision: {decision['action']} (Reason: {decision['reason']})

Your Task:
1. Synthesize these findings into a concise reasoning list.
2. Generate an optimized "Product Search Query" based on all verified entities.
3. Identify cross-domain contradictions (Photo vs Title vs Specs).

Return in strict JSON format:
{{
  "product_search_query": "string",
  "final_errors": {{
    "photo_quality_error": boolean,
    "title_quality_error": boolean,
    "title_contradiction_error": boolean,
    "specs_quality_error": boolean,
    "specs_contradiction_error": boolean,
    "photo_category_error": boolean,
    "title_category_error": boolean,
    "category_contradiction_error": boolean
  }},
  "reasons": ["string"]
}}
"""
