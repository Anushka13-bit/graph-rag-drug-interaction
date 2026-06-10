"""Graph exploration endpoints."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from api.schemas import EntityGraphResponse
from config.settings import Settings, get_settings
from graph import graph_queries as gq
from graph.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["graph"])


def _client(settings: Settings) -> Neo4jClient:
    return Neo4jClient(
        settings.neo4j_uri,
        settings.neo4j_username,
        settings.neo4j_password,
        settings.neo4j_database,
    )


@router.get("/entity/{name}", response_model=EntityGraphResponse)
async def entity_neighborhood(name: str, settings: Settings = Depends(get_settings)) -> EntityGraphResponse:
    client = _client(settings)
    try:
        inter = client.execute_query(gq.GET_DRUG_INTERACTIONS, {"drug_name": name, "limit": 50})
        neigh = client.execute_query(gq.GET_NEIGHBORHOOD, {"drug_name": name, "limit": 50})
        return EntityGraphResponse(entity=name, interactions=inter, neighborhood=neigh)
    except Exception as e:
        logger.exception("graph entity error: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        client.close()


@router.get("/interactions/{drug1}/{drug2}")
async def interactions_between(
    drug1: str,
    drug2: str,
    settings: Settings = Depends(get_settings),
) -> List[Dict[str, Any]]:
    client = _client(settings)
    try:
        return client.execute_query(
            gq.GET_MULTI_HOP_INTERACTIONS,
            {"drug1": drug1, "drug2": drug2, "limit": 20},
        )
    finally:
        client.close()


@router.get("/stats")
async def graph_stats(settings: Settings = Depends(get_settings)) -> Dict[str, int]:
    client = _client(settings)
    try:
        rows = client.execute_query(
            """
            MATCH (n)
            WITH count(n) AS nodes
            MATCH ()-[r]->()
            RETURN nodes, count(r) AS rels
            """,
            {},
        )
        if not rows:
            return {"nodes": 0, "relationships": 0}
        return {
            "nodes": int(rows[0].get("nodes") or 0),
            "relationships": int(rows[0].get("rels") or 0),
        }
    finally:
        client.close()
