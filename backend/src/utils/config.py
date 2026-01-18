"""Application configuration using pydantic-settings."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    environment: str = "development"
    log_level: str = "INFO"
    api_rate_limit: int = 100
    
    # Supabase
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_key: Optional[str] = None
    
    # OpenAI
    openai_api_key: Optional[str] = None
    
    # Anthropic
    anthropic_api_key: Optional[str] = None
    
    # Cohere
    cohere_api_key: Optional[str] = None
    
    # LangSmith
    langsmith_api_key: Optional[str] = None
    langsmith_project: str = "investment-research-ai"
    
    # Tavily (Web Search)
    tavily_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
