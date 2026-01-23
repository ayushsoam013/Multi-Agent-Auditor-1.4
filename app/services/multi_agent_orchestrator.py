import asyncio
import time
import uuid
import logging
from typing import List, Optional, Dict, Any, cast, Union
from app.schemas.agent_schemas import (
    AgentRequest,
    MultiAgentAuditResult,
    PhotoAgentResponse,
    TitleAgentResponse,
    SpecsAgentResponse,
    CategoryAgentResponse,
    RCAAgentResponse,
    MasterAgentResponse,
    BaseAgentResponse,
)
from app.services.agents.photo_agent import PhotoAgent
from app.services.agents.title_agent import TitleAgent
from app.services.agents.specs_agent import SpecsAgent
from app.services.agents.category_agent import CategoryAgent
from app.services.agents.rca_agent import RCAAgent
from app.services.agents.master_agent import MasterAgent

logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:
    """
    Orchestrates the multi-agent auditing pipeline.
    Manages agent dependencies, parallel execution, and result consolidation.
    """

    def __init__(self):
        # Initialize all specialized agents
        self.photo_agent = PhotoAgent()
        self.title_agent = TitleAgent()
        self.specs_agent = SpecsAgent()
        self.category_agent = CategoryAgent()
        self.rca_agent = RCAAgent()
        self.master_agent = MasterAgent()

    async def run_audit(self, request: AgentRequest) -> MultiAgentAuditResult:
        """
        Executes the full audit pipeline for a given product request.

        PIPELINE FLOW:
        1. Parallel Phase: Run Photo, Title, and Specs agents simultaneously to minimize latency.
        2. Conditional Phase: Run Category Agent only if no major 'outliers' (fatal flaws)
           were detected in Phase 1.
        3. Synthesis Phase: Run RCA Agent to perform cross-modal analysis on all previous results.
        4. Decision Phase: Run Master Agent to apply the final Decision Grid/Truth Table.
        """
        audit_id = f"audit_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        start_time = time.time()

        logger.info(f"Starting Multi-Agent Audit v2: {audit_id}")

        if request.context is None:
            request.context = {}

        # 1. Parallel Execution of Base Agents (I/O Bound)
        results_list = await asyncio.gather(
            self.photo_agent.process(request),
            self.title_agent.process(request),
            self.specs_agent.process(request),
            return_exceptions=True,
        )

        # Ensure results_list is a list
        results = cast(List[Any], results_list)

        # Process results with explicit types
        def get_typed_res(res: Any, name: str, cls: Any) -> Any:
            if isinstance(res, Exception):
                return self._error_response(name, res, cls)
            if isinstance(res, cls):
                return res
            return self._error_response(
                name, Exception(f"Unexpected type {type(res)}"), cls
            )

        photo_res: PhotoAgentResponse = get_typed_res(
            results[0], "PhotoAgent", PhotoAgentResponse
        )
        title_res: TitleAgentResponse = get_typed_res(
            results[1], "TitleAgent", TitleAgentResponse
        )
        specs_res: SpecsAgentResponse = get_typed_res(
            results[2], "SpecsAgent", SpecsAgentResponse
        )

        # 2. Conditional Category Agent Execution
        category_res: Optional[CategoryAgentResponse] = None

        # Inject Photo Agent results into context for Category Agent
        request.context["photo_agent"] = photo_res

        if not self._has_outliers(photo_res, title_res, specs_res):
            logger.info(f"No outliers detected. Running CategoryAgent for {audit_id}")
            try:
                cat_output = await self.category_agent.process(request)
                category_res = cast(CategoryAgentResponse, cat_output)
            except Exception as e:
                category_res = self._error_response(
                    "CategoryAgent", e, CategoryAgentResponse
                )
        else:
            logger.info(
                f"Outliers detected or agent failure. Skipping CategoryAgent for {audit_id}"
            )

        # 3. RCA Agent Execution
        request.context["agent_results"] = {
            "photo": photo_res,
            "title": title_res,
            "specs": specs_res,
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
            + title_res.cost
            + specs_res.cost
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
            title_agent=title_res,
            specs_agent=specs_res,
            category_agent=category_res,
            rca_agent=rca_res,
            master_agent=master_res,
            total_processing_time=total_time,
            total_cost=total_cost,
        )

    def _has_outliers(
        self,
        photo: PhotoAgentResponse,
        title: TitleAgentResponse,
        specs: SpecsAgentResponse,
    ) -> bool:
        """
        Check if any agent detected major outliers or failed.
        """
        if (
            photo.status == "failure"
            or title.status == "failure"
            or specs.status == "failure"
        ):
            return True

        # Check Photo outliers
        if photo.analysis and photo.analysis.task_4:
            for val in photo.analysis.task_4.values():
                if getattr(val, "status", None) == "outlier":
                    return True

        # Check Title outliers
        if title.analysis:
            if title.analysis.task_1:
                for val in title.analysis.task_1.values():
                    if getattr(val, "status", None) == "outlier":
                        return True
            if title.analysis.task_4:
                for val in title.analysis.task_4.values():
                    if getattr(val, "status", None) == "outlier":
                        return True

        # Check Specs outliers
        if specs.analysis and specs.analysis.contradictions:
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
