"""Tests for hybrid retrieval helpers."""

from __future__ import annotations

from retrieval.context_assembler import assemble_context
from retrieval.graph_retriever import GraphContext
from retrieval.hybrid_retriever import HybridHit, HybridRetriever


def test_hybrid_mentions_drug() -> None:
    assert HybridRetriever._mentions_any_drug("Warfarin dose", {"warfarin"})


def test_assemble_context_formats_sections() -> None:
    hits = [
        HybridHit(
            chunk_id="1",
            text="t1",
            source="s1",
            final_score=0.9,
            metadata={},
        )
    ]
    ctx = GraphContext(
        direct_interactions=[{"drug1": "a", "drug2": "b", "interaction_type": "effect", "evidence": "e"}],
        multi_hop_paths=[{"drug_chain": ["a", "c", "b"], "hops": 2}],
        neighborhood=[{"relation": "TREATS", "neighbor_name": "x", "neighbor_type": "Disease"}],
    )
    out = assemble_context(hits, ctx)
    assert "Semantic Evidence" in out
    assert "Direct Interactions" in out
