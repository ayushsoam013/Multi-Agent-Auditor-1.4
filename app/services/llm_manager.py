from app.services.gemini_gen_service import gemini_gen_service
from app.services.gemini_service import gemini_service
from app.services.litellm_service import litellm_service

class LLMManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMManager, cls).__new__(cls)
            cls._instance.active_provider = "gemini" # Default
            # Mapping for generation service
            cls._instance.gen_services = {
                "gemini": gemini_gen_service,
                "litellm": litellm_service
            }
            # Mapping for embedding service
            cls._instance.emb_services = {
                "gemini": gemini_service,
                "litellm": litellm_service
            }
        return cls._instance

    def get_service(self):
        """Returns the generation service"""
        return self.gen_services.get(self.active_provider, gemini_gen_service)

    def get_embedding_service(self):
        """Returns the embedding service"""
        return self.emb_services.get(self.active_provider, gemini_service)

    def set_provider(self, provider_name: str):
        if provider_name in self.gen_services:
            self.active_provider = provider_name
        else:
            raise ValueError(f"Unknown provider: {provider_name}")

    def get_current_provider(self) -> str:
        return self.active_provider

llm_manager = LLMManager()
