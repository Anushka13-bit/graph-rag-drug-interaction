"""Parameterized Cypher queries for graph retrieval."""

from __future__ import annotations

GET_DRUG_INTERACTIONS = """
MATCH (d1:Drug {name: $drug_name})-[r:INTERACTS_WITH|CAUSES|TREATS]->(d2)
RETURN d1.name AS drug1, type(r) AS relation, d2.name AS drug2,
       r.type AS interaction_type, r.confidence AS confidence, r.evidence AS evidence
ORDER BY r.confidence DESC
LIMIT $limit
"""

GET_MULTI_HOP_INTERACTIONS = """
MATCH path = (d1:Drug {name: $drug1})-[:INTERACTS_WITH|CAUSES|TREATS*1..3]-(d2:Drug {name: $drug2})
RETURN [node IN nodes(path) | coalesce(node.name, node.description)] AS drug_chain,
       [rel IN relationships(path) | type(rel)] AS interaction_types,
       length(path) AS hops
ORDER BY hops ASC
LIMIT $limit
"""

GET_DRUG_CONTEXT_CHUNKS = """
MATCH (d:Drug {name: $drug_name})-[:MENTIONED_IN]->(c:Chunk)
RETURN c.chunk_id AS chunk_id, c.text AS text, c.source AS source
LIMIT $limit
"""

GET_SHARED_INTERACTIONS = """
MATCH (d1:Drug {name: $drug1})-[:INTERACTS_WITH|CAUSES|TREATS]->(shared)<-[:INTERACTS_WITH|CAUSES|TREATS]-(d2:Drug {name: $drug2})
RETURN shared.name AS shared_drug
"""

GET_NEIGHBORHOOD = """
MATCH (d:Drug {name: $drug_name})-[r]-(neighbor)
RETURN type(r) AS relation,
       labels(neighbor)[0] AS neighbor_type,
       coalesce(neighbor.name, neighbor.description) AS neighbor_name,
       r.type AS interaction_type
LIMIT $limit
"""

LIST_DRUG_NAMES = """
MATCH (d:Drug)
RETURN collect(d.name) AS names
"""
