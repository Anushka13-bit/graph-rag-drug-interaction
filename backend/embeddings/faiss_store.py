"""FAISS fallback vector store."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from config.settings import Settings, get_settings


def _index_path(settings: Settings) -> Path:
    base = Path("./data/embeddings")
    base.mkdir(parents=True, exist_ok=True)
    return base / "faiss_index"


def build_index(documents: List[Document], settings: Settings | None = None) -> FAISS:
    """Build and persist a FAISS index from documents."""
    settings = settings or get_settings()
    embeddings = settings.get_embeddings()
    store = FAISS.from_documents(documents, embeddings)
    path = str(_index_path(settings))
    store.save_local(path)
    return store


def load_index(settings: Settings | None = None) -> FAISS:
    """Load FAISS index from disk."""
    settings = settings or get_settings()
    path = str(_index_path(settings))
    if not os.path.isdir(path):
        raise FileNotFoundError(f"FAISS index not found at {path}")
    embeddings: Embeddings = settings.get_embeddings()
    return FAISS.load_local(
        path,
        embeddings,
        allow_dangerous_deserialization=True,
    )


def search(query: str, top_k: int = 5, settings: Settings | None = None) -> List[Document]:
    """Similarity search against persisted FAISS index."""
    store = load_index(settings)
    return store.similarity_search(query, k=top_k)
