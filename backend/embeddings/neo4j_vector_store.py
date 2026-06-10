"""Neo4j vector index helpers and similarity search."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from graph.graph_queries import GET_NEIGHBORHOOD
from graph.neo4j_client import Neo4jClient
from graph.schema import vector_index_ddl

logger = logging.getLogger(__name__)


class Neo4jVectorStore:
    """Create/manage vector index and run vector + graph-augmented search."""

    def __init__(
        self,
        client: Neo4jClient,
        index_name: str,
        dimensions: int,
    ) -> None:
        self.client = client
        self.index_name = index_name
        self.dimensions = dimensions

    def ensure_vector_index(self) -> None:
        """Create vector index if missing (idempotent)."""
        ddl = vector_index_ddl(self.index_name, self.dimensions)
        try:
            self.client.execute_write(ddl.strip(), {})
        except Exception as e:
            logger.warning("Vector index creation skipped or failed: %s", e)

    def store_chunk_embedding(self, chunk_id: str, embedding: List[float]) -> None:
        cypher = """
        MATCH (c:Chunk {chunk_id: $chunk_id})
        SET c.embedding = $embedding
        """
        self.client.execute_write(cypher, {"chunk_id": chunk_id, "embedding": embedding})

    def similarity_search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Vector search using db.index.vector.queryNodes."""
        cypher = """
        CALL db.index.vector.queryNodes($index_name, $k, $embedding)
        YIELD node, score
        RETURN node.chunk_id AS chunk_id, node.text AS text, node.source AS source, score
        ORDER BY score DESC
        """
        try:
            return self.client.execute_query(
                cypher,
                {"index_name": self.index_name, "k": top_k, "embedding": query_embedding},
            )
        except Exception as e:
            logger.error("Neo4j vector search failed: %s", e)
            raise

    def similarity_search_with_graph_context(
        self,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Augment each hit with one-hop neighborhood from linked drugs."""
        hits = self.similarity_search(query_embedding, top_k=top_k)
        enriched: List[Dict[str, Any]] = []
        for row in hits:
            drugs = self._drugs_for_chunk(row.get("chunk_id"))
            neighbors: List[Dict[str, Any]] = []
            for d in drugs[:3]:
                try:
                    nb = self.client.execute_query(
                        GET_NEIGHBORHOOD,
                        {"drug_name": d, "limit": 5},
                    )
                    neighbors.extend(nb)
                except Exception as e:
                    logger.debug("neighbor fetch failed for %s: %s", d, e)
            item = dict(row)
            item["graph_neighbors"] = neighbors
            enriched.append(item)
        return enriched

    def _drugs_for_chunk(self, chunk_id: Optional[str]) -> List[str]:
        if not chunk_id:
            return []
        cypher = """
        MATCH (d:Drug)-[:MENTIONED_IN]->(c:Chunk {chunk_id: $chunk_id})
        RETURN collect(d.name) AS names
        """
        rows = self.client.execute_query(cypher, {"chunk_id": chunk_id})
        if not rows:
            return []
        return list(rows[0].get("names") or [])
