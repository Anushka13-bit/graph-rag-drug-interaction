"""LangChain LCEL Graph-RAG chain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterator, List

from langchain_core.output_parsers import StrOutputParser

from config.settings import Settings, get_settings
from graph.neo4j_client import Neo4jClient
from reasoning.answer_validator import validate_answer
from reasoning.llm_client import get_chat_model
from reasoning.prompts import build_prompt
from retrieval.context_assembler import assemble_context
from retrieval.hybrid_retriever import HybridRetriever


@dataclass
class RAGResponse:
    answer: str
    sources: List[str]
    graph_paths: List[Dict[str, Any]]
    confidence: str
    interaction_type: str | None


class GraphRAGChain:
    """Hybrid retrieval + prompt + LLM."""

    def __init__(
        self,
        client: Neo4jClient,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.client = client
        self.llm = get_chat_model(self.settings)
        self.retriever = HybridRetriever(self.client, self.settings, graph_llm=self.llm)
        self.prompt = build_prompt()
        self._lc_chain = self.prompt | self.llm | StrOutputParser()

    def invoke(self, question: str) -> RAGResponse:
        hits, gctx = self.retriever.retrieve_with_context(question, top_k=5)
        context = assemble_context(hits, gctx)
        answer = self._lc_chain.invoke({"context": context, "question": question})
        validated = validate_answer(answer, context)
        sources = sorted({h.source for h in hits if h.source})
        return RAGResponse(
            answer=validated.text,
            sources=list(sources),
            graph_paths=list(gctx.multi_hop_paths),
            confidence=validated.confidence,
            interaction_type=validated.interaction_type,
        )

    def stream(self, question: str) -> Iterator[str]:
        hits, gctx = self.retriever.retrieve_with_context(question, top_k=5)
        context = assemble_context(hits, gctx)
        for token in self._lc_chain.stream({"context": context, "question": question}):
            yield token
