import json
import logging
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.services.agents.base_agent import BaseAgent
from app.core.decision_grid import decision_grid_loader
from app.schemas.agent_schemas import (
    AgentRequest,
    MasterAgentResponse,
    PhotoAgentResponse,
    TextualAgentResponse,
    RCAAgentResponse,
    CrossValidation,
    FinalErrors,
)

logger = logging.getLogger(__name__)


class MasterAgent(BaseAgent):
    """
    The Master Agent acts as the final decision maker in the multi-agent pipeline.
    It synthesizes findings from all specialized agents (via the RCA results)
    and applies a deterministic "Decision Grid" to produce a final audit verdict.
    """

    def __init__(self, model_name: Optional[str] = None):
        super().__init__(
            agent_name="MasterAgent",
            model_name=model_name or settings.GEMINI_GEN_MODEL,
            response_class=MasterAgentResponse,
        )

    async def _process_logic(self, request: AgentRequest) -> Dict[str, Any]:
        """
        Master Agent logic (v3 - CSV Grid):
        1. Receive RCA result and other agent outputs from the request context.
        2. Map findings to the 5 specific Decision Grid flags (photo_category, title_category, etc.).
        3. Look up the final decision in the exhaustive truth table (Decision Grid).
        4. Generate a human-readable, polite recommendation for the seller if issues exist.
        """
        context = request.context or {}
        agent_results = context.get("agent_results", {})
        rca_res: Optional[RCAAgentResponse] = context.get("rca_result")
        textual_res: Optional[TextualAgentResponse] = agent_results.get("textual")

        # 1. Extract Search Query from Textual Agent (used for SEO/Searchability check)
        search_query = ""
        if textual_res and textual_res.analysis and textual_res.analysis.task_4:
            search_query = textual_res.analysis.task_4.product_search_query

        # 2. Extract Facts (The 5 binary flags required by the Truth Table)
        facts = self._extract_facts_from_rca(rca_res)

        # 3. Apply New Decision Grid (Truth Table Lookup)
        decision_text, decision_code = self._get_decision_from_grid(facts)

        # Determine Status/Action (PASS/FAIL/REVIEW) based on decision text
        rec_cost = 0.0
        if not decision_text or decision_text.strip() == "":
            action = "PASS"
            decision_text = "Audit Passed"
        else:
            if "Rejected" in decision_text:
                action = "FAIL"
            else:
                action = "REVIEW"

        # Generate Polite Recommendation using LLM based on the identified issues (or lack thereof)
        (
            seller_recommendation,
            rec_cost,
        ) = await self._generate_seller_recommendation(decision_text, rca_res, request)

        # 4. Construct Final Response
        reasons = [decision_text]
        if rca_res and rca_res.analysis:
            reasons.append(f"Root Cause: {rca_res.analysis.root_cause_summary}")
            for issue in rca_res.analysis.identified_issues:
                reasons.append(f"{issue.issue_type}: {issue.description}")

        final_errors = self._populate_final_errors(facts, rca_res)

        return {
            "product_search_query": search_query,
            "rca": rca_res.analysis.dict() if rca_res and rca_res.analysis else None,
            "audit_decision": action,
            "decision_code": decision_code,
            "seller_recommendation": seller_recommendation,
            "confidence_score": 1.0,
            "reasons": reasons,
            "final_errors": final_errors.model_dump(),
            "cross_validation": {
                "photo_title_contradiction": facts["photo_title"],
                "photo_specs_contradiction": facts["photo_specs"],
                "title_specs_contradiction": facts["title_specs"],
                "search_query_contradiction": False,
            },
            "_cost": rec_cost if "rec_cost" in locals() else 0.0,
        }

    async def _generate_seller_recommendation(
        self,
        decision_text: str,
        rca_res: Optional[RCAAgentResponse],
        request: AgentRequest,
    ) -> tuple[str, float]:
        """
        Generates a polite, logical 2-line recommendation for the seller.
        Returns (recommendation_text, cost)
        """
        try:
            issues_str = ""
            if rca_res and rca_res.analysis:
                issues_str = "\n".join(
                    [f"- {i.description}" for i in rca_res.analysis.identified_issues]
                )

            prompt = f"""
            You are a polite quality assurance expert. A product listing has been audited.
            
            AUDIT OUTCOME: {decision_text}
            SPECIFIC ISSUES FOUND:
            {issues_str if issues_str else "None. The product looks good."}
            
            PRODUCT TITLE: {request.product_title}
            
            TASK: Write a polite, reasonable, and helpful recommendation to the seller.
            - If passed: Congratulate them on a high-quality listing.
            - If issues found: Suggest improvements based on specific errors.
            - Tone: Suggestive, polite, and logical.
            - Length: Strictly no more than 2 lines.
            
            RECOMMENDATION:
            """

            # Use chat_with_usage to get cost
            response = await self.gen_service.chat_with_usage(
                messages=[{"role": "user", "content": prompt}]
            )
            return response.get("content", "").strip(), response.get("costing", 0.0)
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return (
                f"Please review your product listing details (Title, Photo, and Specs) to ensure they are consistent and accurate.",
                0.0,
            )

    def _extract_facts_from_rca(
        self, rca_res: Optional[RCAAgentResponse]
    ) -> Dict[str, bool]:
        """
        Maps RCA issues to the 5 binary flags required by the decision grid.
        """
        facts = {
            "photo_category": False,
            "title_category": False,
            "photo_title": False,
            "photo_specs": False,
            "title_specs": False,
        }

        if not rca_res or not rca_res.analysis:
            return facts

        for issue in rca_res.analysis.identified_issues:
            issue_type = issue.issue_type.upper().strip()

            # Mapping RCA issue types to the 5 grid flags
            if "CATEGORY" in issue_type:
                if "PHOTO" in issue_type:
                    facts["photo_category"] = True
                if "TITLE" in issue_type:
                    facts["title_category"] = True

            if (
                "PHOTO" in issue_type
                and "TITLE" in issue_type
                and ("CONTRADICTION" in issue_type or "MISMATCH" in issue_type)
            ):
                facts["photo_title"] = True

            if (
                "PHOTO" in issue_type
                and "SPECS" in issue_type
                and ("CONTRADICTION" in issue_type or "MISMATCH" in issue_type)
            ):
                facts["photo_specs"] = True

            if (
                "TITLE" in issue_type
                and "SPECS" in issue_type
                and ("CONTRADICTION" in issue_type or "MISMATCH" in issue_type)
            ):
                facts["title_specs"] = True

        return facts

    def _get_decision_from_grid(self, facts: Dict[str, bool]) -> tuple[str, str]:
        """
        Implements the 32-row truth table from 'auditmate messging - Sheet2.csv'.
        Returns (English Message, Rule Code)
        """
        return decision_grid_loader.get_decision_text(facts)

    def _populate_final_errors(
        self, facts: Dict[str, bool], rca_res: Optional[RCAAgentResponse]
    ) -> FinalErrors:
        fe = FinalErrors()
        fe.photo_category_error = facts["photo_category"]
        fe.title_category_error = facts["title_category"]
        fe.title_contradiction_error = facts["photo_title"] or facts["title_specs"]
        fe.specs_contradiction_error = facts["photo_specs"] or facts["title_specs"]
        fe.category_contradiction_error = (
            facts["photo_category"] or facts["title_category"]
        )

        if rca_res and rca_res.analysis:
            for issue in rca_res.analysis.identified_issues:
                issue_type = issue.issue_type.upper()
                if "PHOTO_QUALITY" in issue_type:
                    fe.photo_quality_error = True
                if "TITLE_QUALITY" in issue_type:
                    fe.title_quality_error = True
                if "SPECS_QUALITY" in issue_type:
                    fe.specs_quality_error = True
        return fe
