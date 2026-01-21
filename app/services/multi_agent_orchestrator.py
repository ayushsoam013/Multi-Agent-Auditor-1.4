import asyncio
import time
import uuid
import logging
from typing import List, Optional, Dict, Any
from app.schemas.agent_schemas import (
    AgentRequest, 
    MultiAgentAuditResult,
    PhotoAgentResponse,
    TitleAgentResponse,
    SpecsAgentResponse,
    MasterAgentResponse
)
from app.services.agents.photo_agent import PhotoAgent
from app.services.agents.title_agent import TitleAgent
from app.services.agents.specs_agent import SpecsAgent
from app.services.agents.master_agent import MasterAgent

logger = logging.getLogger(__name__)

class MultiAgentOrchestrator:
    def __init__(self):
        self.photo_agent = PhotoAgent()
        self.title_agent = TitleAgent()
        self.specs_agent = SpecsAgent()
        self.master_agent = MasterAgent()

    async def run_audit(self, request: AgentRequest) -> MultiAgentAuditResult:
        audit_id = f"audit_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        start_time = time.time()
        
        logger.info(f"Starting Multi-Agent Audit: {audit_id}")
        
        # 1. Specialized Agent Execution
        # PhotoAgent and SpecsAgent can run in parallel
        # But TitleAgent now needs PhotoAgent output.
        # So we run Photo + Specs, then Title.
        
        parallel_results = await asyncio.gather(
            self.photo_agent.process(request),
            self.specs_agent.process(request),
            return_exceptions=True
        )
        
        photo_res, specs_res = parallel_results
        
        # Handle potential exceptions
        if isinstance(photo_res, Exception): photo_res = self._error_response("PhotoAgent", photo_res)
        if isinstance(specs_res, Exception): specs_res = self._error_response("SpecsAgent", specs_res)

        # Inject PhotoAgent result into context for TitleAgent
        # Note: Agents return Response objects, not dicts
        if getattr(photo_res, "status", None) == "success" and getattr(photo_res, "analysis", None):
            request.context["photo_analysis"] = photo_res.analysis
        
        # Now run TitleAgent with the enriched context
        title_res = await self.title_agent.process(request)
        if isinstance(title_res, Exception): title_res = self._error_response("TitleAgent", title_res)

        # 2. Aggregation and Master Decision
        # Inject all agent results into context for the Master Agent
        request.context["agent_results"] = {
            "photo": photo_res,
            "title": title_res,
            "specs": specs_res
        }
        
        master_res = await self.master_agent.process(request)
        
        total_time = time.time() - start_time
        logger.info(f"Audit {audit_id} completed in {total_time:.2f}s")
        
        return MultiAgentAuditResult(
            audit_id=audit_id,
            photo_agent=photo_res,
            title_agent=title_res,
            specs_agent=specs_res,
            master_agent=master_res,
            total_processing_time=total_time
        )

    def _error_response(self, agent_name: str, e: Exception) -> Dict[str, Any]:
        logger.error(f"Agent {agent_name} failed with exception: {str(e)}")
        return {
            "agent_name": agent_name,
            "status": "failure",
            "error_message": str(e)
        }

orchestrator = MultiAgentOrchestrator()
