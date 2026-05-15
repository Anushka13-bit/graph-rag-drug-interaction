"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import graph as graph_routes
from api.routes import ingest as ingest_routes
from api.routes import query as query_routes
from config.settings import get_settings
from embeddings.neo4j_vector_store import Neo4jVectorStore
from graph.neo4j_client import Neo4jClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    client = Neo4jClient(
        settings.neo4j_uri,
        settings.neo4j_username,
        settings.neo4j_password,
        settings.neo4j_database,
    )
    try:
        try:
            ok = client.health_check()
            if not ok:
                logger.warning("Neo4j health check failed at startup (is Docker Neo4j running?)")
            else:
                vs = Neo4jVectorStore(
                    client,
                    index_name=settings.neo4j_vector_index_name,
                    dimensions=settings.embedding_dimension,
                )
                try:
                    vs.ensure_vector_index()
                except Exception as e:
                    logger.warning("Vector index ensure failed: %s", e)
        except Exception as e:
            logger.warning("Neo4j startup skipped: %s", e)
    finally:
        client.close()
    yield


app = FastAPI(title="Biomedical Graph-RAG", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query_routes.router)
app.include_router(ingest_routes.router)
app.include_router(graph_routes.router)


@app.get("/health")
async def health() -> dict[str, str]:
    settings = get_settings()
    client = Neo4jClient(
        settings.neo4j_uri,
        settings.neo4j_username,
        settings.neo4j_password,
        settings.neo4j_database,
    )
    try:
        ok = client.health_check()
        return {"status": "ok" if ok else "degraded", "neo4j": "up" if ok else "down"}
    finally:
        client.close()
