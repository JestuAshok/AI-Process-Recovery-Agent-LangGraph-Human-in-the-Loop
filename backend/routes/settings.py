from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from backend.config import settings
from backend.agent.llm import llm_service

router = APIRouter(prefix="/api/settings", tags=["Settings & Configuration"])


class SettingsUpdate(BaseModel):
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_api_key: Optional[str] = None
    auto_recovery_enabled: Optional[bool] = None
    max_recovery_retries: Optional[int] = None
    approval_severity_threshold: Optional[str] = None
    require_approval_for_replacements: Optional[bool] = None


@router.get("")
def get_settings():
    """Returns current system configuration."""
    has_key = bool(settings.LLM_API_KEY)
    masked_key = f"{settings.LLM_API_KEY[:4]}...{settings.LLM_API_KEY[-4:]}" if (settings.LLM_API_KEY and len(settings.LLM_API_KEY) > 8) else ("Configured" if has_key else "None (Using Deterministic Heuristic Engine)")

    return {
        "project_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database_url": settings.DATABASE_URL,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "llm_api_key_status": masked_key,
        "has_llm_api_key": has_key,
        "auto_recovery_enabled": settings.AUTO_RECOVERY_ENABLED,
        "max_recovery_retries": settings.MAX_RECOVERY_RETRIES,
        "approval_severity_threshold": settings.APPROVAL_SEVERITY_THRESHOLD,
        "require_approval_for_replacements": settings.REQUIRE_APPROVAL_FOR_REPLACEMENTS,
        "active_llm_mode": "LangChain External Model" if llm_service._llm else "Built-in Structured Heuristic Engine (Offline/Zero-Key Mode)"
    }


@router.post("")
def update_settings(req: SettingsUpdate):
    """Updates runtime configuration settings."""
    if req.llm_provider is not None:
        settings.LLM_PROVIDER = req.llm_provider
    if req.llm_model is not None:
        settings.LLM_MODEL = req.llm_model
    if req.llm_api_key is not None:
        settings.LLM_API_KEY = req.llm_api_key
    if req.auto_recovery_enabled is not None:
        settings.AUTO_RECOVERY_ENABLED = req.auto_recovery_enabled
    if req.max_recovery_retries is not None:
        settings.MAX_RECOVERY_RETRIES = req.max_recovery_retries
    if req.approval_severity_threshold is not None:
        settings.APPROVAL_SEVERITY_THRESHOLD = req.approval_severity_threshold
    if req.require_approval_for_replacements is not None:
        settings.REQUIRE_APPROVAL_FOR_REPLACEMENTS = req.require_approval_for_replacements

    # Re-initialize LLM client
    llm_service.provider = settings.LLM_PROVIDER
    llm_service.model_name = settings.LLM_MODEL
    llm_service.api_key = settings.LLM_API_KEY
    llm_service._init_llm_client()

    return {"status": "SUCCESS", "message": "Settings updated successfully."}
