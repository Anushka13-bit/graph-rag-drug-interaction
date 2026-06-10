#!/usr/bin/env python3
"""Interactive CLI for querying the Graph-RAG system."""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config.settings import get_settings
from graph.neo4j_client import Neo4jClient
from reasoning.rag_chain import GraphRAGChain


def main() -> None:
    settings = get_settings()
    print("Biomedical Graph-RAG CLI. Type 'exit' to quit.")
    while True:
        q = input("Question> ").strip()
        if not q or q.lower() in {"exit", "quit"}:
            break
        client = Neo4jClient(
            settings.neo4j_uri,
            settings.neo4j_username,
            settings.neo4j_password,
            settings.neo4j_database,
        )
        try:
            chain = GraphRAGChain(client, settings)
            resp = chain.invoke(q)
            print(resp.answer)
            print(f"[confidence={resp.confidence}, type={resp.interaction_type}]")
        finally:
            client.close()


if __name__ == "__main__":
    main()
