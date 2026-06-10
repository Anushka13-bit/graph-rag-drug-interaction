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
            subject="DrugA",
            predicate="INTERACTS_WITH_EFFECT",
            object="DrugB",
            interaction_type="effect",
            confidence=1.0,
            evidence_text="ev1",
        ),
        ExtractedRelation(
            subject="DrugA",
            predicate="CAUSES",
            object="DiseaseX",
            confidence=0.9,
            evidence_text="ev2",
        ),
        ExtractedRelation(
            subject="DrugB",
            predicate="TREATS",
            object="DiseaseY",
            confidence=0.85,
            evidence_text="ev3",
        ),
        ExtractedRelation(
            subject="DrugA",
            predicate="INHIBITS",
            object="Mech1",
            confidence=0.95,
            evidence_text="ev4",
        ),
        ExtractedRelation(
            subject="DrugB",
            predicate="INDUCES",
            object="Mech2",
            confidence=0.75,
            evidence_text="ev5",
        ),
    ]
    gb.batch_upsert_relations(c, rels)
    assert len(c.writes) > 0
    queries = [q for q, _ in c.writes]
    assert any("INTERACTS_WITH" in q for q in queries)
    assert any("CAUSES" in q for q in queries)
    assert any("TREATS" in q for q in queries)
    assert any("INHIBITS" in q for q in queries)
    assert any("INDUCES" in q for q in queries)
