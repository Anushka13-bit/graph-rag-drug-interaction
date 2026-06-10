#!/usr/bin/env python3
"""Apply Neo4j constraints, btree indexes, and vector index."""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config.settings import get_settings
from graph.neo4j_client import Neo4jClient
from graph.schema import CONSTRAINTS_AND_INDEXES, vector_index_ddl


def main() -> None:
    settings = get_settings()
    client = Neo4jClient(
        settings.neo4j_uri,
        settings.neo4j_username,
        settings.neo4j_password,
        settings.neo4j_database,
    )
    try:
        for stmt in CONSTRAINTS_AND_INDEXES:
            client.execute_write(stmt.strip(), {})
        ddl = vector_index_ddl(settings.neo4j_vector_index_name, settings.embedding_dimension)
        client.execute_write(ddl.strip(), {})
        print("Schema and vector index ensured.")
    finally:
        client.close()


if __name__ == "__main__":
    main()
