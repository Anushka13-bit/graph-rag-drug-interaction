"""Embedding backends for vector search."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from langchain_openai import OpenAIEmbeddings

from config.settings import Settings


class BaseEmbedder(ABC):
    """Abstract embedding interface."""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        raise NotImplementedError

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError


class LocalEmbedder(BaseEmbedder):
    """sentence-transformers backend."""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)

    def embed_text(self, text: str) -> List[float]:
        vec = self._model.encode(text, convert_to_numpy=True)
        return vec.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        mat = self._model.encode(texts, convert_to_numpy=True)
        return [row.tolist() for row in mat]


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


def get_embedder(settings: Settings) -> BaseEmbedder:
    """Factory for local or OpenAI embedders based on settings."""
    if settings.use_openai:
        return OpenAIEmbedder(settings)
    return LocalEmbedder(settings.embedding_model)
