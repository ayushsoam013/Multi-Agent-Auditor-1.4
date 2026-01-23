import asyncio
import time
import uuid
import logging
from typing import List, Optional, Dict, Any, cast, Union
from app.schemas.agent_schemas import (
    AgentRequest,
    MultiAgentAuditResult,
    PhotoAgentResponse,
    TextualAgentResponse,
    CategoryAgentResponse,
    RCAAgentResponse,
    MasterAgentResponse,
    BaseAgentResponse,
    CodeReviewAgentResponse,
)
from app.services.agents.photo_agent import PhotoAgent
from app.services.agents.textual_agent import TextualAgent
from app.services.agents.category_agent import CategoryAgent
from app.services.agents.rca_agent import RCAAgent
from app.services.agents.master_agent import MasterAgent
from app.services.agents.code_review_agent import CodeReviewAgent

logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:
    """
    Orchestrates the multi-agent auditing pipeline.
    Manages agent dependencies, parallel execution, and result consolidation.
    """

    def __init__(self):
        # Initialize all specialized agents
        self.photo_agent = PhotoAgent()
        self.textual_agent = TextualAgent()
        self.category_agent = CategoryAgent()
        self.rca_agent = RCAAgent()
        self.master_agent = MasterAgent()
        self.code_review_agent = CodeReviewAgent()

    async def run_audit(self, request: AgentRequest) -> MultiAgentAuditResult:
        """
        Executes the full audit pipeline for a given product request.

        PIPELINE FLOW:
        1. Parallel Phase: Run Photo and Textual agents simultaneously.
        2. Conditional Phase: Run Category Agent only if no major 'outliers' detected.
        3. Synthesis Phase: Run RCA Agent to perform cross-modal analysis.
        4. Decision Phase: Run Master Agent to apply the final Decision Grid.
        """
        audit_id = f"audit_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        start_time = time.time()

        logger.info(f"Starting Multi-Agent Audit v2: {audit_id}")

        if request.context is None:
            request.context = {}

        # 1. Parallel Execution of Base Agents (I/O Bound)
        # We need to run PhotoAgent first or in parallel?
        # TextualAgent requires PhotoAgent output for the prompt.
        # So we cannot run them fully in parallel if TextualAgent depends on PhotoAgent output.
        # Wait, the prompt instruction said: "Photo Agent Output (Textual Only): ..."
        # And my implementation of TextualAgent reads `request.context["photo_agent"]`.
        # This implies sequential dependency: Photo -> Textual.

        # Let's check the dependency.
        # TextualAgent uses `request.context.get("photo_agent")`.
        # So PhotoAgent MUST run before TextualAgent.

        # Step 1: Run Photo Agent
        try:
            photo_output = await self.photo_agent.process(request)
            photo_res: PhotoAgentResponse = cast(PhotoAgentResponse, photo_output)
        except Exception as e:
            photo_res = self._error_response("PhotoAgent", e, PhotoAgentResponse)

        # Inject Photo Agent results into context for Textual Agent and others
        request.context["photo_agent"] = photo_res

        # Step 2: Run Textual Agent (which now has photo context)
        try:
            textual_output = await self.textual_agent.process(request)
            textual_res: TextualAgentResponse = cast(
                TextualAgentResponse, textual_output
            )
        except Exception as e:
            textual_res = self._error_response("TextualAgent", e, TextualAgentResponse)

        # 2. Conditional Category Agent Execution
        category_res: Optional[CategoryAgentResponse] = None

        if not self._has_outliers(photo_res, textual_res):
            logger.info(f"No outliers detected. Running CategoryAgent for {audit_id}")
            # try:
            #     cat_output = await self.category_agent.process(request)
            #     category_res = cast(CategoryAgentResponse, cat_output)
            # except Exception as e:
            #     category_res = self._error_response(
            #         "CategoryAgent", e, CategoryAgentResponse
            #     )
            logger.info("CategoryAgent is disabled.")
        else:
            logger.info(
                f"Outliers detected or agent failure. Skipping CategoryAgent for {audit_id}"
            )

        # 3. RCA Agent Execution
        request.context["agent_results"] = {
            "photo": photo_res,
            "textual": textual_res,
            "category": category_res,
        }

        rca_res: RCAAgentResponse
        try:
            rca_output = await self.rca_agent.process(request)
            rca_res = cast(RCAAgentResponse, rca_output)
        except Exception as e:
            rca_res = self._error_response("RCAAgent", e, RCAAgentResponse)

        # 4. Master Agent Execution (Decision Grid)
        request.context["rca_result"] = rca_res
        master_res: MasterAgentResponse
        try:
            master_output = await self.master_agent.process(request)
            master_res = cast(MasterAgentResponse, master_output)
        except Exception as e:
            master_res = self._error_response("MasterAgent", e, MasterAgentResponse)

        total_time = time.time() - start_time

        total_cost = (
            photo_res.cost
            + textual_res.cost
            + (category_res.cost if category_res else 0.0)
            + rca_res.cost
            + master_res.cost
        )

        logger.info(
            f"Audit {audit_id} completed in {total_time:.2f}s with cost ${total_cost:.6f}"
        )

        return MultiAgentAuditResult(
            audit_id=audit_id,
            photo_agent=photo_res,
            textual_agent=textual_res,
            category_agent=category_res,
            rca_agent=rca_res,
            master_agent=master_res,
            total_processing_time=total_time,
            total_cost=total_cost,
        )

    async def run_code_review(self, request: AgentRequest) -> CodeReviewAgentResponse:
        """
        Executes the code review agent.
        """
        try:
            output = await self.code_review_agent.process(request)
            return cast(CodeReviewAgentResponse, output)
        except Exception as e:
            # We need to cast to Any to avoid type checking issues with _error_response return type
            return cast(
                CodeReviewAgentResponse,
                self._error_response("CodeReviewAgent", e, CodeReviewAgentResponse),
            )

    def _has_outliers(
        self,
        photo: PhotoAgentResponse,
        textual: TextualAgentResponse,
    ) -> bool:
        """
        Check if any agent detected major outliers or failed.
        """
        if photo.status == "failure" or textual.status == "failure":
            return True

        # Check Photo outliers
        if photo.analysis and photo.analysis.task_4:
            for val in photo.analysis.task_4.values():
                if getattr(val, "status", None) == "outlier":
                    return True

        # Check Textual outliers
        if textual.analysis:
            # Task 1: Title Assessment
            if textual.analysis.task_1:
                if (
                    textual.analysis.task_1.spell_error.status == "outlier"
                    or textual.analysis.task_1.duplicate_words.status == "outlier"
                    or textual.analysis.task_1.internal_contradiction.status
                    == "outlier"
                ):
                    return True

            # Task 2: Specs Assessment
            if textual.analysis.task_2:
                if (
                    textual.analysis.task_2.spell_error.status == "outlier"
                    or textual.analysis.task_2.duplicate_specifications.status
                    == "outlier"
                    or textual.analysis.task_2.internal_contradiction.status
                    == "outlier"
                ):
                    return True

            # Task 5: Cross-Modal Verification
            if textual.analysis.task_5:
                # Iterate over fields in task_5
                for field_name in textual.analysis.task_5.model_fields:
                    val = getattr(textual.analysis.task_5, field_name)
                    if getattr(val, "status", None) == "outlier":
                        return True

            # Task 6: Category Verification
            if textual.analysis.task_6:
                for field_name in textual.analysis.task_6.model_fields:
                    val = getattr(textual.analysis.task_6, field_name)
                    if getattr(val, "status", None) == "outlier":
                        return True

            # Task 7: Advanced Integrity Checks
            if textual.analysis.task_7:
                for field_name in textual.analysis.task_7.model_fields:
                    val = getattr(textual.analysis.task_7, field_name)
                    if getattr(val, "status", None) == "outlier":
                        return True

        return False

    def _error_response(
        self, agent_name: str, e: Exception, response_class: Any
    ) -> Any:
        logger.error(f"Agent {agent_name} failed with exception: {str(e)}")
        return response_class(
            agent_name=agent_name, status="failure", error_message=str(e)
        )


orchestrator = MultiAgentOrchestrator()
