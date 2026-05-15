"""Cypher DDL for constraints, btree indexes, and vector index."""

from __future__ import annotations

CONSTRAINTS_AND_INDEXES: list[str] = [
    """
    CREATE CONSTRAINT drug_name_unique IF NOT EXISTS
    FOR (d:Drug) REQUIRE d.name IS UNIQUE
    """,
    """
    CREATE CONSTRAINT disease_name_unique IF NOT EXISTS
    FOR (d:Disease) REQUIRE d.name IS UNIQUE
    """,
    """
    CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS
    FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE
    """,
    """
    CREATE INDEX drug_name_index IF NOT EXISTS FOR (d:Drug) ON (d.name)
    """,
    """
    CREATE INDEX chunk_source_index IF NOT EXISTS FOR (c:Chunk) ON (c.source)
    """,
]


def vector_index_ddl(index_name: str, dimensions: int) -> str:
    """Return CREATE VECTOR INDEX statement for Chunk.embedding."""
    if not index_name.replace("_", "").isalnum():
        raise ValueError("vector index name must be alphanumeric with underscores")
    return f"""
    CREATE VECTOR INDEX {index_name} IF NOT EXISTS
    FOR (c:Chunk) ON (c.embedding)
    OPTIONS {{
      indexConfig: {{
        `vector.dimensions`: {int(dimensions)},
        `vector.similarity_function`: 'cosine'
      }}
    }}
    """
