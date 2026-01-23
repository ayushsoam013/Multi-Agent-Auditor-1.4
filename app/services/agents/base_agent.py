import asyncio
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.schemas.agent_schemas import AgentRequest, BaseAgentResponse
from app.services.llm_manager import llm_manager

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract Base Class for all specialized agents (Photo, Title, Specs, etc.).
    Provides a standardized execution flow, error handling, and performance/cost tracking.
    """

    def __init__(
        self,
        agent_name: str,
        model_name: Optional[str] = None,
        response_class: type = BaseAgentResponse,
    ):
        self.agent_name = agent_name
        self.model_name = model_name
        self.response_class = response_class
        # Uses the global LLM manager to get the configured generation service (Gemini/LiteLLM)
        self.gen_service = llm_manager.get_service()

    async def process(self, request: AgentRequest) -> BaseAgentResponse:
        """
        Main entry point for agent processing.
        Handles the lifecycle of a request: timing, validation, core logic, and error wrapping.
        """
        start_time = time.time()
        try:
            # Step 1: Optional validation hook for subclass-specific requirements
            self._validate_input(request)

            # Step 2: Execute specific agent logic (implemented in subclasses)
            result_data = await self._process_logic(request)

            # Step 3: Extract cost metadata if returned by the LLM service
            cost = 0.0
            if isinstance(result_data, dict):
                cost = result_data.pop("_cost", 0.0)

            processing_time = time.time() - start_time

            # Step 4: Wrap results in the appropriate response schema
            return self._create_response(
                status="success",
                processing_time=processing_time,
                cost=cost,
                raw_output=result_data,
            )

        except Exception as e:
            # Standardized error handling ensures the orchestrator doesn't crash
            # if a single agent fails.
            processing_time = time.time() - start_time
            logger.error(f"Error in {self.agent_name}: {str(e)}", exc_info=True)
            return self._create_response(
                status="failure", error_message=str(e), processing_time=processing_time
            )

    @abstractmethod
    async def _process_logic(self, request: AgentRequest) -> Dict[str, Any]:
        """
        Specific logic for each agent. Must be implemented by subclasses.
        """
        pass

    def _validate_input(self, request: AgentRequest):
        """
        Hook for input validation. Can be overridden by subclasses.
        """
        pass

    def _create_response(self, **kwargs) -> BaseAgentResponse:
        """
        Helper to create a standard response object.
        """
        raw_output = kwargs.get("raw_output")

        # If we have analysis data in raw_output, and the response class supports it
        if raw_output and self.response_class != BaseAgentResponse:
            kwargs["analysis"] = raw_output

            # If the response class has specific fields that are also in raw_output,
            # we can try to populate them for better accessibility.
            # This is especially useful for the "Dumb" MasterAgent.
            if isinstance(raw_output, dict):
                for field_name in self.response_class.model_fields:
                    if field_name in raw_output and field_name not in kwargs:
                        kwargs[field_name] = raw_output[field_name]

        return self.response_class(agent_name=self.agent_name, **kwargs)
