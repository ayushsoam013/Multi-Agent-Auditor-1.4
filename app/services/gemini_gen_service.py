from google import genai
from google.genai import types
from typing import List, Optional, Dict, Any
from app.core.config import settings

class GeminiGenService:
    def __init__(self, model_name: Optional[str] = None):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
        
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = model_name or settings.GEMINI_GEN_MODEL

    async def generate_content(self, prompt: str, config: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates content based on a text prompt.
        """
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config
        )
        return response.text

    async def chat(self, messages: List[Dict[str, str]], config: Optional[Dict[str, Any]] = None) -> str:
        """
        Simple chat interface wrapper.
        Expects messages in format: [{"role": "user", "parts": "..."}]
        """
        # Note: google.genai has specific message types. 
        # For simplicity, we'll convert simple dicts to Content objects if needed or use the client direct.
        # Here we use the simplified contents list approach.
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=messages,
            config=config
        )
        return response.text

    async def chat_with_usage(self, messages: List[Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Chat interface returning content and usage.
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
                    parts=[types.Part(text=content)] if isinstance(content, str) else content
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
                system_instruction=system_instruction,
                **cfg
            )

        response = self.client.models.generate_content(
            model=model_name,
            contents=formatted_messages,
            config=gen_config
        )
        
        usage = None
        if response.usage_metadata:
            usage = {
                "prompt_tokens": response.usage_metadata.prompt_token_count,
                "completion_tokens": response.usage_metadata.candidates_token_count,
                "total_tokens": response.usage_metadata.total_token_count
            }
            
        return {
            "content": response.text,
            "usage": usage,
            "model": model_name
        }

    def health_check(self) -> bool:
        try:
            # Quick ping
            self.client.models.generate_content(
                model=self.model_name,
                contents="ping",
                config=types.GenerateContentConfig(max_output_tokens=1)
            )
            return True
        except Exception:
            return False

gemini_gen_service = GeminiGenService()
