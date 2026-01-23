import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "Embeddings Optimization API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "local")  # local or prod

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_GEN_MODEL: str = os.getenv("GEMINI_GEN_MODEL", "gemini-2.5-flash-lite")
    LITELLM_API_KEY: str = os.getenv("LITELLM_API_KEY", "")

    # LiteLLM default models (without litellm_proxy/ prefix - will be added in service layer)
    LITELLM_DEFAULT_MODEL: str = os.getenv(
        "LITELLM_DEFAULT_MODEL", "google/gemini-2.5-flash-lite"
    )

    class Config:
        case_sensitive = True


settings = Settings()
