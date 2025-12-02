import os
from functools import lru_cache
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseModel):
    """Application settings configuration."""
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field("gpt-4o", description="OpenAI model to use")
    app_name: str = Field("LLM Service", description="Name of the application")
    debug: bool = Field(False, description="Debug mode")
    
    # Azure OpenAI specific settings
    use_azure: bool = Field(True, description="Whether to use Azure OpenAI")
    azure_endpoint: str = Field("", description="Azure OpenAI endpoint")
    azure_api_version: str = Field("2024-02-15-preview", description="Azure OpenAI API version")


@lru_cache()
def get_settings() -> Settings:
    """
    Create and return a Settings object with values from environment variables.
    The function is cached so settings are loaded only once.
    """
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        debug=os.getenv("DEBUG", "false").lower() == "true",
        use_azure=os.getenv("USE_AZURE", "true").lower() == "true",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        azure_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
    )
