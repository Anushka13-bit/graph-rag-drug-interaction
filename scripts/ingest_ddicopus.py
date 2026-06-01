#!/usr/bin/env python3
"""CLI: ingest DDICorpus (Brat Train+Test or XML) into Neo4j and vector indexes."""

from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config.settings import get_settings
from graph.neo4j_client import Neo4jClient
from ingestion.pipeline import IngestionPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest DDICorpus Brat or XML")
    parser.add_argument(
        "--data-dir",
        default="./data/raw/DDICorpusBrat 2",
        help="Brat corpus root (with Train/ and Test/) or XML folder",
    )
    args = parser.parse_args()
    settings = get_settings()
    client = Neo4jClient(
        settings.neo4j_uri,
        settings.neo4j_username,
        settings.neo4j_password,
        settings.neo4j_database,
    )
    try:
        pipe = IngestionPipeline(client, settings)
        stats = pipe.run_ddicopus(args.data_dir)
        print("Ingestion complete:", stats)
    finally:
        client.close()


if __name__ == "__main__":
    main()
