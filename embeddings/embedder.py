"""Embedding backends: HuggingFace (local), Ollama, or OpenAI."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import List

from langchain_openai import OpenAIEmbeddings

from config.settings import Settings

logger = logging.getLogger(__name__)

# Ollama pull names (not HuggingFace repos)
OLLAMA_EMBEDDING_MODELS = frozenset(
    {
        "nomic-embed-text",
        "mxbai-embed-large",
        "snowflake-arctic-embed",
        "snowflake-arctic-embed2",
        "bge-m3",
        "all-minilm",
    }
)

DEFAULT_HF_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_HF_DIMENSION = 384


class BaseEmbedder(ABC):
    """Abstract embedding interface."""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        raise NotImplementedError

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    @property
    def dimension(self) -> int | None:
        """Output vector size, if known."""
        return None


class LocalEmbedder(BaseEmbedder):
    """sentence-transformers / HuggingFace models."""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        hf_name = model_name
        if "/" not in hf_name and not hf_name.startswith("sentence-transformers"):
            hf_name = f"sentence-transformers/{hf_name}"
        logger.info("Loading HuggingFace embedding model: %s", hf_name)
        self._model = SentenceTransformer(hf_name)
        dim_fn = getattr(self._model, "get_embedding_dimension", None) or getattr(
            self._model, "get_sentence_embedding_dimension"
        )
        self._dimension = int(dim_fn())

    def embed_text(self, text: str) -> List[float]:
        vec = self._model.encode(text, convert_to_numpy=True)
        return vec.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        mat = self._model.encode(texts, convert_to_numpy=True)
        return [row.tolist() for row in mat]

    @property
    def dimension(self) -> int | None:
        return self._dimension


class OllamaEmbedder(BaseEmbedder):
    """Ollama embeddings API (e.g. nomic-embed-text). Requires `ollama serve` and `ollama pull <model>`."""

    def __init__(self, settings: Settings) -> None:
        from langchain_ollama import OllamaEmbeddings

        self._model_name = settings.embedding_model
        self._dimension = settings.embedding_dimension
        logger.info(
            "Using Ollama embeddings: %s at %s (dim=%s)",
            self._model_name,
            settings.ollama_base_url,
            self._dimension,
        )
        self._emb = OllamaEmbeddings(
            model=self._model_name,
            base_url=settings.ollama_base_url,
        )

    def embed_text(self, text: str) -> List[float]:
        return list(self._emb.embed_query(text))

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        return [list(v) for v in self._emb.embed_documents(texts)]

    @property
    def dimension(self) -> int | None:
        return self._dimension


class OpenAIEmbedder(BaseEmbedder):
    """OpenAI embeddings via LangChain."""

    def __init__(self, settings: Settings) -> None:
        self._emb = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model="text-embedding-3-small",
        )

    def embed_text(self, text: str) -> List[float]:
        return list(self._emb.embed_query(text))

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        return [list(v) for v in self._emb.embed_documents(texts)]


def resolve_embedding_backend(settings: Settings) -> str:
    """Return one of: openai, ollama, huggingface."""
    if settings.use_openai:
        return "openai"
    backend = (settings.embedding_backend or "auto").lower()
    if backend in ("ollama", "huggingface", "hf", "local"):
        return "ollama" if backend == "ollama" else "huggingface"
    name = settings.embedding_model.strip().lower()
    if name in OLLAMA_EMBEDDING_MODELS or "nomic-embed" in name:
        return "ollama"
    if name.startswith("sentence-transformers/") or name.startswith("sentence-transformers\\"):
        return "huggingface"
    if "/" not in name and "minilm" not in name and "bert" not in name:
        return "ollama"
    return "huggingface"


def get_embedder(settings: Settings) -> BaseEmbedder:
    """Factory for OpenAI, Ollama, or HuggingFace embedders."""
    backend = resolve_embedding_backend(settings)
    if backend == "openai":
        return OpenAIEmbedder(settings)
    if backend == "ollama":
        return OllamaEmbedder(settings)
    return LocalEmbedder(settings.embedding_model)
