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


class InteractionDetail(BaseModel):
    """Structured drug interaction detail for visualization."""
    drug_a: str
    drug_b: str
    interaction_type: str
    severity: Literal["mild", "moderate", "severe"] = "moderate"
    description: str
    evidence_count: int = 1
    sources: List[str] = Field(default_factory=list)


class DrugInteractionResponse(BaseModel):
    """Response for drug interaction queries."""
    drugs_queried: List[str] = Field(default_factory=list)
    interactions: List[InteractionDetail] = Field(default_factory=list)
    graph_data: Dict[str, Any] = Field(default_factory=dict)
    summary: str = ""
    total_interactions: int = 0
