"""Format retrieved evidence for LLM consumption."""

from __future__ import annotations

from typing import List

from retrieval.graph_retriever import GraphContext
from retrieval.hybrid_retriever import HybridHit


def assemble_context(vector_results: List[HybridHit], graph_context: GraphContext) -> str:
    """Merge hybrid vector hits and graph context into a single prompt block."""
    lines: List[str] = []
    lines.append("## Semantic Evidence (from document chunks):")
    if not vector_results:
        lines.append("(none)")
    for h in vector_results:
        lines.append(f"{h.text} (Source: {h.source})")

    lines.append("\n## Knowledge Graph Evidence:")
    lines.append("### Direct Interactions:")
    if graph_context.direct_interactions:
        for row in graph_context.direct_interactions:
            d1 = row.get("drug1")
            d2 = row.get("drug2")
            rel = row.get("relation") or "INTERACTS_WITH"
            it = row.get("interaction_type")
            ev = row.get("evidence")
            if it:
                lines.append(f"- {d1} {rel} {d2}: {it} — \"{ev}\"")
            else:
                lines.append(f"- {d1} {rel} {d2} — \"{ev}\"")
    else:
        lines.append("(none)")

    lines.append("\n### Multi-hop Paths:")
    if graph_context.multi_hop_paths:
        for row in graph_context.multi_hop_paths:
            chain = row.get("drug_chain")
            hops = row.get("hops")
            lines.append(f"- {' → '.join(str(x) for x in (chain or []))} ({hops} hops)")
    else:
        lines.append("(none)")

    lines.append("\n### Neighborhood Context:")
    if graph_context.neighborhood:
        for row in graph_context.neighborhood:
            rel = row.get("relation")
            nn = row.get("neighbor_name")
            nt = row.get("neighbor_type")
            lines.append(f"- {rel} → {nn} ({nt})")
    else:
        lines.append("(none)")
    return "\n".join(lines)
