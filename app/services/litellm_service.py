import litellm
import requests
from typing import List, Dict, Optional, Any
from app.core.config import settings


class LiteLLMService:
    """
    Integration service for LiteLLM Proxy.
    Handles model routing, proxy authentication, and standardized cost tracking.
    """

    def __init__(self, model_name: str = None):
        # Read from environment variables or use defaults (without litellm_proxy/ prefix)
        default_model = getattr(
            settings, "LITELLM_DEFAULT_MODEL", "google/gemini-2.5-flash-lite"
        )

        self.model_name = model_name or default_model
        # Proxy base URL (Internal network)
        self.api_base = "https://imllm.intermesh.net/v1"
        self.api_key = (
            settings.LITELLM_API_KEY or settings.GEMINI_API_KEY
        )  # Fallback/Usage

    def _ensure_litellm_proxy_prefix(self, model_name: str) -> str:
        """
        LiteLLM Proxy requires a 'litellm_proxy/' prefix to route requests correctly.
        This helper ensures all model strings conform to this requirement.
        """
        if model_name.startswith("litellm_proxy/"):
            return model_name
        else:
            return f"litellm_proxy/{model_name}"

    async def generate_content(
        self, prompt: str, config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generates content based on a text prompt using LiteLLM.
        """
        messages = [{"role": "user", "content": prompt}]

        model_name = self.model_name
        if config and "model" in config:
            model_name = config["model"]

        # Ensure litellm_proxy/ prefix
        model_name = self._ensure_litellm_proxy_prefix(model_name)

        response = await litellm.acompletion(
            model=model_name,
            messages=messages,
            api_base=self.api_base,
            api_key=self.api_key,
            stream=False,
        )

        return response.choices[0].message.content

    async def chat(
        self, messages: List[Dict[str, str]], config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Chat interface wrapper.
        """
        formatted_messages = []
        for msg in messages:
            content = msg.get("content") or msg.get("parts")
            if isinstance(content, list):
                content = " ".join([str(p) for p in content])

            formatted_messages.append(
                {"role": msg.get("role", "user"), "content": content}
            )

        model_name = self.model_name
        if config and "model" in config:
            model_name = config["model"]

        # Ensure litellm_proxy/ prefix
        model_name = self._ensure_litellm_proxy_prefix(model_name)

        response = await litellm.acompletion(
            model=model_name,
            messages=formatted_messages,
            api_base=self.api_base,
            api_key=self.api_key,
            stream=False,
        )

        return response.choices[0].message.content

    async def chat_with_usage(
        self, messages: List[Any], config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Chat interface returning content and usage.
        """
        formatted_messages = []
        for msg in messages:
            if hasattr(msg, "model_dump"):
                m = msg.model_dump()
            elif isinstance(msg, dict):
                m = msg
            else:
                m = {"role": "user", "content": str(msg)}

            content = m.get("content") or m.get("parts")
            if isinstance(content, list):
                content = " ".join([str(p) for p in content])

            formatted_messages.append(
                {"role": m.get("role", "user"), "content": content}
            )

        # Use config for max_tokens and temperature if provided
        kwargs = {}
        model_name = self.model_name
        if config:
            if "max_output_tokens" in config:
                kwargs["max_tokens"] = config["max_output_tokens"]
            if "temperature" in config:
                kwargs["temperature"] = config["temperature"]
            if "model" in config:
                model_name = config["model"]

        # Ensure litellm_proxy/ prefix
        model_name = self._ensure_litellm_proxy_prefix(model_name)

        response = await litellm.acompletion(
            model=model_name,
            messages=formatted_messages,
            api_base=self.api_base,
            api_key=self.api_key,
            stream=False,
            **kwargs,
        )

        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        cost = 0.0
        try:
            cost = litellm.completion_cost(completion_response=response)
        except Exception as e:
            # Fallback or log if cost calculation fails
            print(f"Cost calculation failed: {e}")
            pass

        return {
            "content": response.choices[0].message.content,
            "usage": usage,
            "costing": cost,
            "model": model_name,
        }

    async def health_check(self) -> bool:
        try:
            # User requested specific health check via GET model URL
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    params={
                        "return_wildcard_routes": "false",
                        "include_model_access_groups": "false",
                        "only_model_access_groups": "false",
                        "include_metadata": "false",
                    },
                    timeout=5,
                ) as response:
                    return response.status == 200
        except Exception as e:
            print(f"LiteLLM Health Check Failed: {e}")
            return False


litellm_service = LiteLLMService()
