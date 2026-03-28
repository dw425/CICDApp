"""LLM Configuration — Settings for AI-powered features (remediation, insights)."""

import os


LLM_CONFIG = {
    "provider": os.environ.get("LLM_PROVIDER", "none"),  # none, openai, anthropic, databricks
    "model": os.environ.get("LLM_MODEL", ""),
    "api_key": os.environ.get("LLM_API_KEY", ""),
    "endpoint": os.environ.get("LLM_ENDPOINT", ""),
    "max_tokens": int(os.environ.get("LLM_MAX_TOKENS", "1024")),
    "temperature": float(os.environ.get("LLM_TEMPERATURE", "0.3")),
}


def is_llm_available() -> bool:
    """Check if an LLM provider is configured."""
    return LLM_CONFIG["provider"] != "none" and bool(LLM_CONFIG["api_key"])


def get_llm_config() -> dict:
    """Return current LLM configuration (without API key)."""
    safe = {k: v for k, v in LLM_CONFIG.items() if k != "api_key"}
    safe["available"] = is_llm_available()
    return safe
