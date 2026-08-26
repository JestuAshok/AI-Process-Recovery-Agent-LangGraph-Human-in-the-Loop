import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Process Recovery Agent – LangGraph – Human-in-the-Loop"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "127.0.0.1"

    # Ngrok Settings
    NGROK_URL: Optional[str] = None
    NGROK_AUTH_TOKEN: Optional[str] = None

    # Database
    DATABASE_URL: str = "sqlite:///./recovery_agent.db"

    # LLM Settings
    LLM_PROVIDER: str = "heuristic"  # heuristic, openai, gemini, anthropic
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_API_KEY: Optional[str] = None
    LLM_TEMPERATURE: float = 0.1

    # Recovery Engine Rules
    AUTO_RECOVERY_ENABLED: bool = True
    MAX_RECOVERY_RETRIES: int = 3
    APPROVAL_SEVERITY_THRESHOLD: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    REQUIRE_APPROVAL_FOR_REPLACEMENTS: bool = True
    CHAOS_MODE_ENABLED: bool = False

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
