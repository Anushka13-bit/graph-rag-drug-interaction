"""Tests for graph builder batch helpers."""

from __future__ import annotations

from typing import Any, List, Mapping

from graph import graph_builder as gb
from ingestion.relation_extractor import ExtractedRelation


class FakeClient:
    def __init__(self) -> None:
        self.writes: List[tuple[str, Mapping[str, Any]]] = []

    def execute_write(self, cypher: str, params: Mapping[str, Any]) -> List[Mapping[str, Any]]:
        self.writes.append((cypher, params))
        return []


def test_batch_upsert_drugs() -> None:
    c = FakeClient()
    gb.batch_upsert_drugs(c, ["aspirin", "aspirin", ""])
    assert any("UNWIND" in q for q, _ in c.writes)


def test_batch_upsert_relations() -> None:
    c = FakeClient()
    rels = [
        ExtractedRelation(
            subject="a",
            predicate="INTERACTS_WITH_EFFECT",
            object="b",
            interaction_type="effect",
            confidence=1.0,
            evidence_text="ev",
        )
    ]
    gb.batch_upsert_relations(c, rels)
    assert c.writes
