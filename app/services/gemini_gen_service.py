from google import genai
from google.genai import types
from typing import List, Optional, Dict, Any
from app.core.config import settings


class GeminiGenService:
    """
    Direct integration service for Google Gemini API.
    Provides multi-modal support (text/image) and granular cost calculation.
    """

    def __init__(self, model_name: Optional[str] = None):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")

        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = model_name or settings.GEMINI_GEN_MODEL

    async def chat_with_usage(
        self, messages: List[Any], config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes a chat request and extracts token usage metadata.
        Returns a dictionary containing the content, usage statistics, and calculated cost.
        """
        formatted_messages = []
        system_instruction = None

        for msg in messages:
            if hasattr(msg, "model_dump"):
                m = msg.model_dump()
            elif isinstance(msg, dict):
                m = msg
            else:
                m = {"role": "user", "content": str(msg)}

            role = m.get("role")
            content = m.get("content")

            if role == "system":
                system_instruction = content
                continue

            if role == "assistant":
                role = "model"

            formatted_messages.append(
                types.Content(
                    role=role,
                    parts=[types.Part(text=content)]
                    if isinstance(content, str)
                    else content,
                )
            )

        model_name = self.model_name

        # Prepare Config
        gen_config = None
        if config or system_instruction:
            cfg = config.copy() if config else {}
            if "model" in cfg:
                model_name = cfg.pop("model")

            # Map max_output_tokens to max_output_tokens (it is already)
            # Map temperature to temperature (it is already)

            gen_config = types.GenerateContentConfig(
                system_instruction=system_instruction, **cfg
            )

        response = self.client.models.generate_content(
            model=model_name, contents=formatted_messages, config=gen_config
        )

        usage = None
        if response.usage_metadata:
            usage = {
                "prompt_tokens": response.usage_metadata.prompt_token_count or 0,
                "completion_tokens": response.usage_metadata.candidates_token_count
                or 0,
                "total_tokens": response.usage_metadata.total_token_count or 0,
            }

        cost = self._calculate_cost(model_name, usage)

        return {
            "content": response.text,
            "usage": usage,
            "costing": cost,
            "model": model_name,
        }

    def _calculate_cost(self, model: str, usage: Optional[Dict[str, int]]) -> float:
        """
        Calculate cost in USD based on model and usage.
        Pricing (per 1M tokens):
        - gemini-1.5-flash: $0.075 input, $0.30 output
        - gemini-1.5-pro: $3.50 input, $10.50 output
        - gemini-2.0-flash: $0.10 input, $0.40 output (Estimated)
        """
        if not usage:
            return 0.0

        # Normalize model name
        model = model.lower()

        # Pricing table (per 1M tokens)
        pricing = {
            "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
            "gemini-1.5-pro": {"input": 3.50, "output": 10.50},
            "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
            "gemini-2.5-flash-lite": {"input": 0.075, "output": 0.30},
        }

        # Default to highest if unknown, or 0? Let's default to flash pricing as fallback or 0.
        # Finding the closest match
        rates = None
        for key in pricing:
            if key in model:
                rates = pricing[key]
                break

        if not rates:
            # Fallback to 1.5 flash rates if unknown
            rates = pricing["gemini-1.5-flash"]

        input_cost = (usage["prompt_tokens"] / 1_000_000) * rates["input"]
        output_cost = (usage["completion_tokens"] / 1_000_000) * rates["output"]

        return round(input_cost + output_cost, 6)

    def health_check(self) -> bool:
        try:
            # Quick ping
            self.client.models.generate_content(
                model=self.model_name,
                contents="ping",
                config=types.GenerateContentConfig(max_output_tokens=1),
            )
            return True
        except Exception:
            return False


gemini_gen_service = GeminiGenService()
