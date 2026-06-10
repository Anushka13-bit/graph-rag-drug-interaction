"""Ingestion API routes."""

from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends

from api.schemas import IngestRequest
from config.settings import Settings, get_settings
from graph.neo4j_client import Neo4jClient
from ingestion.pipeline import IngestionPipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingest"])

_status: dict[str, str | int] = {
    "state": "idle",
    "last_message": "",
}


def _run_ingest(data_type: Literal["ddicopus", "pdf"], path: str, settings: Settings) -> None:
    global _status
    client = Neo4jClient(
        settings.neo4j_uri,
        settings.neo4j_username,
        settings.neo4j_password,
        settings.neo4j_database,
    )
    try:
        pipe = IngestionPipeline(client, settings)
        if data_type == "ddicopus":
            stats = pipe.run_ddicopus(path)
        else:
            stats = pipe.run_pdfs(path)
        _status["state"] = "done"
        _status["last_message"] = str(stats)
    except Exception as e:
        logger.exception("ingestion failed: %s", e)
        _status["state"] = "error"
        _status["last_message"] = str(e)
    finally:
        client.close()


@router.post("")
async def start_ingest(
    body: IngestRequest,
    background: BackgroundTasks,
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    global _status
    _status = {"state": "running", "last_message": body.path}
    background.add_task(_run_ingest, body.data_type, body.path, settings)
    return {"status": "accepted"}


@router.get("/status")
async def ingest_status() -> dict[str, str | int]:
    return dict(_status)
