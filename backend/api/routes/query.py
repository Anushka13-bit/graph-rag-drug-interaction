"""Query endpoint for Graph-RAG DDI reasoning."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, AsyncIterator, Dict, List

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from api.schemas import (
    DrugInteractionResponse,
    InteractionDetail,
    QueryRequest,
    QueryResponse,
)
from config.settings import Settings, get_settings
from graph.neo4j_client import Neo4jClient
from reasoning.rag_chain import GraphRAGChain
from retrieval.graph_retriever import GraphRetriever

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])


def _parse_severity(text: str) -> str:
    """Heuristic severity from interaction description or type."""
    low = text.lower()
    if any(w in low for w in ("severe", "critical", "contraindicated", "fatal", "dangerous")):
        return "severe"
    if any(w in low for w in ("moderate", "significant", "caution", "monitor")):
        return "moderate"
    return "mild"


def _build_graph_data(drugs: List[str], interactions: List[InteractionDetail]) -> Dict[str, Any]:
    """Build nodes + edges for frontend D3 visualization."""
    node_set: dict[str, dict] = {}
    edges: list[dict] = []

    for d in drugs:
        node_set[d.lower()] = {"id": d, "label": d, "type": "drug"}

    for ix in interactions:
        a_key = ix.drug_a.lower()
        b_key = ix.drug_b.lower()
        if a_key not in node_set:
            node_set[a_key] = {"id": ix.drug_a, "label": ix.drug_a, "type": "drug"}
        if b_key not in node_set:
            node_set[b_key] = {"id": ix.drug_b, "label": ix.drug_b, "type": "drug"}
        edges.append({
            "source": ix.drug_a,
            "target": ix.drug_b,
            "type": ix.interaction_type,
            "severity": ix.severity,
        })

    return {"nodes": list(node_set.values()), "edges": edges}


def _extract_structured_interactions(
    answer: str,
    graph_paths: List[Dict[str, Any]],
    direct_interactions: List[Dict[str, Any]],
    drugs: List[str],
    top_k: int,
) -> List[InteractionDetail]:
    """Extract concise interaction details from graph data + LLM answer."""
    interactions: list[InteractionDetail] = []
    seen: set[tuple[str, str]] = set()

    # 1. From direct graph interactions
    for row in direct_interactions:
        d1 = row.get("drug1", "")
        d2 = row.get("drug2", "")
        if not d1 or not d2:
            continue
        pair = (min(d1.lower(), d2.lower()), max(d1.lower(), d2.lower()))
        if pair in seen:
            continue
        seen.add(pair)

        itype = row.get("interaction_type") or row.get("relation") or "unknown"
        evidence = row.get("evidence") or ""
        # Truncate long evidence to one sentence
        desc = evidence.split(".")[0].strip() if evidence else f"{d1} interacts with {d2}"
        if len(desc) > 150:
            desc = desc[:147] + "..."

        interactions.append(InteractionDetail(
            drug_a=d1,
            drug_b=d2,
            interaction_type=str(itype),
            severity=_parse_severity(f"{itype} {evidence}"),
            description=desc,
            evidence_count=1,
            sources=[],
        ))

    # 2. From multi-hop paths
    for path in graph_paths:
        chain = path.get("drug_chain", [])
        itypes = path.get("interaction_types", [])
        if len(chain) >= 2:
            d1 = str(chain[0])
            d2 = str(chain[-1])
            pair = (min(d1.lower(), d2.lower()), max(d1.lower(), d2.lower()))
            if pair in seen:
                continue
            seen.add(pair)
            itype = ", ".join(str(t) for t in itypes) if itypes else "indirect"
            interactions.append(InteractionDetail(
                drug_a=d1,
                drug_b=d2,
                interaction_type=itype,
                severity=_parse_severity(itype),
                description=f"Multi-hop path: {' → '.join(str(c) for c in chain)}",
                evidence_count=1,
                sources=[],
            ))

    # 3. If we still have nothing, create a summary interaction from the answer
    if not interactions and len(drugs) >= 2:
        # Parse first line of answer as description
        first_line = answer.split("\n")[0].strip("•- ").strip()
        if len(first_line) > 150:
            first_line = first_line[:147] + "..."
        interactions.append(InteractionDetail(
            drug_a=drugs[0],
            drug_b=drugs[1] if len(drugs) > 1 else "Unknown",
            interaction_type="unknown",
            severity="moderate",
            description=first_line or "Interaction detected — see summary",
            evidence_count=1,
            sources=[],
        ))

    return interactions[:top_k]


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


@router.post("/interact", response_model=DrugInteractionResponse)
async def post_interact(
    body: QueryRequest,
    settings: Settings = Depends(get_settings),
) -> DrugInteractionResponse:
    """Structured interaction endpoint returning top-k concise results with graph data."""
    client = Neo4jClient(
        settings.neo4j_uri,
        settings.neo4j_username,
        settings.neo4j_password,
        settings.neo4j_database,
    )
    try:

        def _run() -> DrugInteractionResponse:
            chain = GraphRAGChain(client, settings)
            graph_ret = GraphRetriever(client, llm=chain.llm)
            drugs = graph_ret.extract_drug_names_from_query(body.question)

            # Get RAG answer (concise prompt)
            resp = chain.invoke(body.question)

            # Retrieve raw graph context for structured cards
            graph_ctx = graph_ret.retrieve(body.question, drugs)

            # Build structured interactions
            interactions = _extract_structured_interactions(
                answer=resp.answer,
                graph_paths=list(graph_ctx.multi_hop_paths),
                direct_interactions=list(graph_ctx.direct_interactions),
                drugs=drugs,
                top_k=body.top_k,
            )

            # Build graph visualization data
            graph_data = _build_graph_data(drugs, interactions)

            # Concise summary — first bullet or first sentence
            summary = resp.answer.strip()
            # Take just the first 2 bullet lines as summary
            lines = [l.strip() for l in summary.split("\n") if l.strip()]
            summary = " | ".join(lines[:2]) if lines else summary
            if len(summary) > 300:
                summary = summary[:297] + "..."

            return DrugInteractionResponse(
                drugs_queried=drugs,
                interactions=interactions,
                graph_data=graph_data,
                summary=summary,
                total_interactions=len(interactions),
            )

        return await asyncio.to_thread(_run)
    except Exception as e:
        logger.exception("interact query failed: %s", e)
        return DrugInteractionResponse(
            drugs_queried=[],
            interactions=[],
            graph_data={"nodes": [], "edges": []},
            summary=f"Error: {e}",
            total_interactions=0,
        )
    finally:
        client.close()
