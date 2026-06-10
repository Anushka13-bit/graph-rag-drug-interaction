"""LLM factory helpers for reasoning chains."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from config.settings import Settings, get_settings


def get_chat_model(settings: Settings | None = None, **kwargs: object) -> BaseChatModel:
    """Return configured chat model (OpenAI or Ollama)."""
    settings = settings or get_settings()
    return settings.get_llm(**kwargs)
