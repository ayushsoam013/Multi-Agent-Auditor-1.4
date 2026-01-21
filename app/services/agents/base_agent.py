import asyncio
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.schemas.agent_schemas import AgentRequest, BaseAgentResponse
from app.services.llm_manager import llm_manager

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, agent_name: str, model_name: Optional[str] = None, response_class: type = BaseAgentResponse):
        self.agent_name = agent_name
        self.model_name = model_name
        self.response_class = response_class
        self.gen_service = llm_manager.get_service()

    async def process(self, request: AgentRequest) -> BaseAgentResponse:
        """
        Main entry point for agent processing.
        Handles timing and error wrapping.
        """
        start_time = time.time()
        try:
            # Optional validation hook
            self._validate_input(request)
            
            # Execute specific agent logic
            result_data = await self._process_logic(request)
            
            processing_time = time.time() - start_time
            
            return self._create_response(
                status="success",
                processing_time=processing_time,
                raw_output=result_data
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error in {self.agent_name}: {str(e)}", exc_info=True)
            return self._create_response(
                status="failure",
                error_message=str(e),
                processing_time=processing_time
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
        # If we have analysis data in raw_output, and the response class supports it
        if "raw_output" in kwargs and self.response_class != BaseAgentResponse:
            kwargs["analysis"] = kwargs["raw_output"]

        return self.response_class(
            agent_name=self.agent_name,
            **kwargs
        )
