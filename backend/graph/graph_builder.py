"""MERGE-based graph construction for drugs, diseases, mechanisms, and chunks."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Mapping, Optional

from graph.neo4j_client import Neo4jClient
from ingestion.relation_extractor import ExtractedRelation

logger = logging.getLogger(__name__)


def upsert_drug(
    client: Neo4jClient,
    name: str,
    aliases: Optional[List[str]] = None,
    drug_type: Optional[str] = None,
) -> None:
    """MERGE a Drug node keyed by normalized name."""
    cypher = """
    MERGE (d:Drug {name: $name})
    SET d.aliases = coalesce($aliases, []),
        d.drug_type = $drug_type
    """
    client.execute_write(
        cypher,
        {"name": name.strip(), "aliases": aliases or [], "drug_type": drug_type},
    )


def upsert_disease(client: Neo4jClient, name: str) -> None:
    client.execute_write(
        "MERGE (d:Disease {name: $name})",
        {"name": name.strip()},
    )


def upsert_mechanism(client: Neo4jClient, description: str) -> None:
    client.execute_write(
        "MERGE (m:Mechanism {description: $description})",
        {"description": description.strip()},
    )


def upsert_chunk(
    client: Neo4jClient,
    chunk_id: str,
    text: str,
    metadata: Mapping[str, Any],
    embedding: Optional[List[float]] = None,
) -> None:
    """MERGE Chunk with optional embedding vector."""
    cypher = """
    MERGE (c:Chunk {chunk_id: $chunk_id})
    SET c.text = $text,
        c.source = $source,
        c.page = $page,
        c.chunk_index = $chunk_index,
        c.embedding = CASE WHEN $embedding IS NULL THEN c.embedding ELSE $embedding END
    """
    page = metadata.get("page") or metadata.get("page_number")
    source = (
        metadata.get("source")
        or metadata.get("source_file")
        or metadata.get("sentence_id")
        or ""
    )
    client.execute_write(
        cypher,
        {
            "chunk_id": chunk_id,
            "text": text,
            "source": str(source),
            "page": page,
            "chunk_index": metadata.get("chunk_index", 0),
            "embedding": embedding,
        },
    )


def link_drug_to_chunk(client: Neo4jClient, drug_name: str, chunk_id: str) -> None:
    cypher = """
    MATCH (d:Drug {name: $drug_name})
    MATCH (c:Chunk {chunk_id: $chunk_id})
    MERGE (d)-[:MENTIONED_IN]->(c)
    """
    client.execute_write(cypher, {"drug_name": drug_name.strip(), "chunk_id": chunk_id})


def upsert_relation(
    client: Neo4jClient,
    subject: str,
    predicate: str,
    object: str,
    properties: Optional[Mapping[str, Any]] = None,
) -> None:
    """Create typed relationship based on predicate label."""
    props = dict(properties or {})
    pred = predicate.upper().strip()
    subj = subject.strip()
    obj = object.strip()

    if pred.startswith("INTERACTS_WITH"):
        itype = props.get("interaction_type") or props.get("type")
        cypher = """
        MERGE (s:Drug {name: $subject})
        MERGE (o:Drug {name: $object})
        MERGE (s)-[r:INTERACTS_WITH]->(o)
        SET r.type = $itype,
            r.confidence = coalesce($confidence, r.confidence, 1.0),
            r.evidence = coalesce($evidence, r.evidence, '')
        """
        client.execute_write(
            cypher,
            {
                "subject": subj,
                "object": obj,
                "itype": itype,
                "confidence": props.get("confidence"),
                "evidence": props.get("evidence") or props.get("evidence_text"),
            },
        )
        return
    if pred == "CAUSES":
        upsert_disease(client, obj)
        cypher = """
        MERGE (s:Drug {name: $subject})
        MERGE (o:Disease {name: $object})
        MERGE (s)-[r:CAUSES]->(o)
        SET r += $extra
        """
        client.execute_write(
            cypher,
            {"subject": subj, "object": obj, "extra": {k: v for k, v in props.items() if k in ("confidence", "evidence", "evidence_text")}},
        )
        return
    if pred == "TREATS":
        upsert_disease(client, obj)
        cypher = """
        MERGE (s:Drug {name: $subject})
        MERGE (o:Disease {name: $object})
        MERGE (s)-[r:TREATS]->(o)
        SET r += $extra
        """
        client.execute_write(
            cypher,
            {"subject": subj, "object": obj, "extra": {k: v for k, v in props.items() if k in ("confidence", "evidence", "evidence_text")}},
        )
        return
    if pred == "INHIBITS":
        upsert_mechanism(client, obj)
        cypher = """
        MERGE (s:Drug {name: $subject})
        MERGE (o:Mechanism {description: $object})
        MERGE (s)-[r:INHIBITS]->(o)
        SET r += $extra
        """
        client.execute_write(
            cypher,
            {"subject": subj, "object": obj, "extra": {k: v for k, v in props.items() if k in ("confidence", "evidence", "evidence_text")}},
        )
        return
    if pred == "INDUCES":
        upsert_mechanism(client, obj)
        cypher = """
        MERGE (s:Drug {name: $subject})
        MERGE (o:Mechanism {description: $object})
        MERGE (s)-[r:INDUCES]->(o)
        SET r += $extra
        """
        client.execute_write(
            cypher,
            {"subject": subj, "object": obj, "extra": {k: v for k, v in props.items() if k in ("confidence", "evidence", "evidence_text")}},
        )
        return

    logger.warning("Unsupported predicate for upsert_relation: %s", predicate)


def batch_upsert_relations(client: Neo4jClient, relations: List[ExtractedRelation]) -> None:
    """Batch MERGE relations of various predicates (INTERACTS_WITH, CAUSES, TREATS, etc.)."""
    from collections import defaultdict
    by_predicate = defaultdict(list)
    for r in relations:
        subj = r.subject.strip()
        obj = r.object.strip()
        if not subj or not obj:
            continue
        pred = (r.predicate or "INTERACTS_WITH").upper().strip()
        if pred.startswith("INTERACTS_WITH"):
            pred = "INTERACTS_WITH"
        by_predicate[pred].append({
            "subject": subj,
            "object": obj,
            "interaction_type": r.interaction_type,
            "confidence": float(r.confidence) if r.confidence is not None else 1.0,
            "evidence": r.evidence_text or "",
        })

    for pred, rows in by_predicate.items():
        if not rows:
            continue
        if pred == "INTERACTS_WITH":
            cypher = """
            UNWIND $rows AS row
            MERGE (s:Drug {name: row.subject})
            MERGE (o:Drug {name: row.object})
            MERGE (s)-[r:INTERACTS_WITH]->(o)
            SET r.type = row.interaction_type,
                r.confidence = row.confidence,
                r.evidence = row.evidence
            """
            client.execute_write(cypher, {"rows": rows})
        elif pred == "CAUSES":
            disease_rows = [{"name": r["object"]} for r in rows]
            client.execute_write("UNWIND $rows AS row MERGE (d:Disease {name: row.name})", {"rows": disease_rows})
            cypher = """
            UNWIND $rows AS row
            MERGE (s:Drug {name: row.subject})
            MERGE (o:Disease {name: row.object})
            MERGE (s)-[r:CAUSES]->(o)
            SET r.confidence = row.confidence,
                r.evidence = row.evidence
            """
            client.execute_write(cypher, {"rows": rows})
        elif pred == "TREATS":
            disease_rows = [{"name": r["object"]} for r in rows]
            client.execute_write("UNWIND $rows AS row MERGE (d:Disease {name: row.name})", {"rows": disease_rows})
            cypher = """
            UNWIND $rows AS row
            MERGE (s:Drug {name: row.subject})
            MERGE (o:Disease {name: row.object})
            MERGE (s)-[r:TREATS]->(o)
            SET r.confidence = row.confidence,
                r.evidence = row.evidence
            """
            client.execute_write(cypher, {"rows": rows})
        elif pred == "INHIBITS":
            mechanism_rows = [{"description": r["object"]} for r in rows]
            client.execute_write("UNWIND $rows AS row MERGE (m:Mechanism {description: row.description})", {"rows": mechanism_rows})
            cypher = """
            UNWIND $rows AS row
            MERGE (s:Drug {name: row.subject})
            MERGE (o:Mechanism {description: row.object})
            MERGE (s)-[r:INHIBITS]->(o)
            SET r.confidence = row.confidence,
                r.evidence = row.evidence
            """
            client.execute_write(cypher, {"rows": rows})
        elif pred == "INDUCES":
            mechanism_rows = [{"description": r["object"]} for r in rows]
            client.execute_write("UNWIND $rows AS row MERGE (m:Mechanism {description: row.description})", {"rows": mechanism_rows})
            cypher = """
            UNWIND $rows AS row
            MERGE (s:Drug {name: row.subject})
            MERGE (o:Mechanism {description: row.object})
            MERGE (s)-[r:INDUCES]->(o)
            SET r.confidence = row.confidence,
                r.evidence = row.evidence
            """
            client.execute_write(cypher, {"rows": rows})
        else:
            logger.warning("Unsupported predicate for batch_upsert_relations: %s", pred)


def link_sequential_chunks(
    client: Neo4jClient,
    chunk_ids: List[str],
    source_file: str,
) -> None:
    """Link consecutive Chunk nodes with FROM_DOCUMENT (sequential chunks)."""
    pairs = [
        {"a": chunk_ids[i], "b": chunk_ids[i + 1]}
        for i in range(len(chunk_ids) - 1)
    ]
    if not pairs:
        return
    cypher = """
    UNWIND $pairs AS p
    MATCH (c1:Chunk {chunk_id: p.a})
    MATCH (c2:Chunk {chunk_id: p.b})
    MERGE (c1)-[rel:FROM_DOCUMENT]->(c2)
    SET rel.source_file = $source_file
    """
    client.execute_write(cypher, {"pairs": pairs, "source_file": source_file})


def batch_upsert_chunks(
    client: Neo4jClient,
    rows: List[Mapping[str, Any]],
) -> None:
    """Bulk MERGE Chunk nodes with optional embeddings."""
    if not rows:
        return
    cypher = """
    UNWIND $rows AS row
    MERGE (c:Chunk {chunk_id: row.chunk_id})
    SET c.text = row.text,
        c.source = row.source,
        c.page = row.page,
        c.chunk_index = row.chunk_index,
        c.embedding = CASE WHEN row.embedding IS NULL THEN c.embedding ELSE row.embedding END
    """
    client.execute_write(cypher, {"rows": list(rows)})


def batch_link_drugs_to_chunks(client: Neo4jClient, links: List[Mapping[str, str]]) -> None:
    """Bulk MENTIONED_IN from drugs to chunks."""
    if not links:
        return
    cypher = """
    UNWIND $links AS row
    MATCH (d:Drug {name: row.drug})
    MATCH (c:Chunk {chunk_id: row.chunk_id})
    MERGE (d)-[:MENTIONED_IN]->(c)
    """
    client.execute_write(cypher, {"links": list(links)})


def batch_upsert_drugs(client: Neo4jClient, names: List[str]) -> None:
    """Bulk MERGE Drug nodes by name."""
    if not names:
        return
    rows = [{"name": n.strip()} for n in names if n and n.strip()]
    if not rows:
        return
    cypher = """
    UNWIND $rows AS row
    MERGE (d:Drug {name: row.name})
    """
    client.execute_write(cypher, {"rows": rows})
