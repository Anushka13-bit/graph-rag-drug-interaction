"""Semantic vector retrieval with Neo4j primary and FAISS fallback."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document

from config.settings import Settings, get_settings
from embeddings.embedder import get_embedder
from embeddings.faiss_store import search as faiss_search
from embeddings.neo4j_vector_store import Neo4jVectorStore
from graph.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    source: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class VectorRetriever:
    """Wraps Neo4j vector search with optional FAISS fallback."""

    def __init__(
        self,
        client: Neo4jClient,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.client = client
        self.embedder = get_embedder(self.settings)
        self._vector = Neo4jVectorStore(
            client,
            index_name=self.settings.neo4j_vector_index_name,
            dimensions=self.settings.embedding_dimension,
        )

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        qvec = self.embedder.embed_text(query)
        try:
            rows = self._vector.similarity_search(qvec, top_k=top_k)
            return [
                RetrievedChunk(
                    chunk_id=str(r.get("chunk_id") or ""),
                    text=str(r.get("text") or ""),
                    source=str(r.get("source") or ""),
                    score=float(r.get("score") or 0.0),
                    metadata={"backend": "neo4j"},
                )
                for r in rows
            ]
        except Exception as e:
            logger.warning("Neo4j vector retrieval failed, falling back to FAISS: %s", e)
            try:
                docs = faiss_search(query, top_k=top_k, settings=self.settings)
                return [
                    RetrievedChunk(
                        chunk_id=str(d.metadata.get("chunk_id") or d.metadata.get("sentence_id") or ""),
                        text=d.page_content,
                        source=str(d.metadata.get("source") or d.metadata.get("source_file") or ""),
                        score=1.0 - (i * 0.01),
                        metadata={"backend": "faiss", **d.metadata},
                    )
                    for i, d in enumerate(docs)
                ]
            except Exception as e2:
                logger.error("FAISS fallback failed: %s", e2)
                return []

    def warm_faiss_from_documents(self, documents: List[Document]) -> None:
        """Persist a FAISS index from documents for fallback search."""
        from embeddings.faiss_store import build_index

        if documents:
            build_index(documents, self.settings)
