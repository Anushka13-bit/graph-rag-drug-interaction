"""Pydantic models for API requests and responses."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    include_graph_paths: bool = True
    stream: bool = False


class QueryResponse(BaseModel):
    answer: str
    interaction_type: Optional[str] = None
    confidence: str
    sources: List[str] = Field(default_factory=list)
    graph_paths: List[Dict[str, Any]] = Field(default_factory=list)
    drugs_detected: List[str] = Field(default_factory=list)


class IngestRequest(BaseModel):
    data_type: Literal["ddicopus", "pdf"]
    path: str


class EntityGraphResponse(BaseModel):
    entity: str
    interactions: List[Dict[str, Any]] = Field(default_factory=list)
    neighborhood: List[Dict[str, Any]] = Field(default_factory=list)
