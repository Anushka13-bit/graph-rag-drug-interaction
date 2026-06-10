"""Hybrid fusion of vector and graph retrieval."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from config.settings import Settings, get_settings
from graph.neo4j_client import Neo4jClient
from retrieval.graph_retriever import GraphContext, GraphRetriever
from retrieval.vector_retriever import RetrievedChunk, VectorRetriever


@dataclass
class HybridHit:
    chunk_id: str
    text: str
    source: str
    final_score: float
    metadata: Dict[str, object] = field(default_factory=dict)


class HybridRetriever:
    """Fuse semantic chunks with graph relevance heuristics."""

    def __init__(
        self,
        client: Neo4jClient,
        settings: Settings | None = None,
        graph_llm=None,
    ) -> None:
        self.settings = settings or get_settings()
        self.vector = VectorRetriever(client, self.settings)
        self.graph = GraphRetriever(client, llm=graph_llm)

    def retrieve_with_context(self, query: str, top_k: int = 5) -> tuple[List[HybridHit], GraphContext]:
        vec_hits = self.vector.retrieve(query, top_k=top_k * 2)
        drugs = self.graph.extract_drug_names_from_query(query)
        graph_ctx = self.graph.retrieve(query, drugs)
        drug_l = {d.lower() for d in drugs}

        merged: Dict[str, HybridHit] = {}
        for ch in vec_hits:
            gscore = 1.0 if self._mentions_any_drug(ch.text, drug_l) else 0.5
            vscore = float(ch.score or 0.0)
            final = 0.6 * vscore + 0.4 * gscore
            prev = merged.get(ch.chunk_id)
            hit = HybridHit(
                chunk_id=ch.chunk_id,
                text=ch.text,
                source=ch.source,
                final_score=final,
                metadata={"vector_score": vscore, "graph_relevance": gscore, **ch.metadata},
            )
            if prev is None or final > prev.final_score:
                merged[ch.chunk_id] = hit

        ranked = sorted(merged.values(), key=lambda h: h.final_score, reverse=True)
        return ranked[:top_k], graph_ctx

    def retrieve(self, query: str, top_k: int = 5) -> List[HybridHit]:
        hits, _ctx = self.retrieve_with_context(query, top_k=top_k)
        return hits

    @staticmethod
    def _mentions_any_drug(text: str, drugs_lower: Set[str]) -> bool:
        low = text.lower()
        return any(d in low for d in drugs_lower)
