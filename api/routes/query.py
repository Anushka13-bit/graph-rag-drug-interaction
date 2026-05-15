"""Query endpoint for Graph-RAG DDI reasoning."""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from api.schemas import QueryRequest, QueryResponse
from config.settings import Settings, get_settings
from graph.neo4j_client import Neo4jClient
from reasoning.rag_chain import GraphRAGChain
from retrieval.graph_retriever import GraphRetriever

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=None)
async def post_query(
    body: QueryRequest,
    settings: Settings = Depends(get_settings),
) -> QueryResponse | StreamingResponse:
    client = Neo4jClient(
        settings.neo4j_uri,
        settings.neo4j_username,
        settings.neo4j_password,
        settings.neo4j_database,
    )
    chain = GraphRAGChain(client, settings)
    graph = GraphRetriever(client, llm=chain.llm)
    drugs = graph.extract_drug_names_from_query(body.question)

    if body.stream:

        async def gen() -> AsyncIterator[bytes]:
            try:
                for token in chain.stream(body.question):
                    yield token.encode("utf-8")
            finally:
                client.close()

        return StreamingResponse(gen(), media_type="text/plain")

    try:

        def _run() -> QueryResponse:
            resp = chain.invoke(body.question)
            paths = resp.graph_paths if body.include_graph_paths else []
            return QueryResponse(
                answer=resp.answer,
                interaction_type=resp.interaction_type,
                confidence=resp.confidence,
                sources=resp.sources,
                graph_paths=paths,
                drugs_detected=drugs,
            )

        return await asyncio.to_thread(_run)
    except Exception as e:
        logger.exception("query failed: %s", e)
        return QueryResponse(
            answer=f"Error processing query: {e}",
            interaction_type=None,
            confidence="Low",
            sources=[],
            graph_paths=[],
            drugs_detected=drugs,
        )
    finally:
        if not body.stream:
            client.close()
