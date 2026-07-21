#!/usr/bin/env python3
"""Check Neo4j ingestion progress — run anytime to see current counts."""

from neo4j import GraphDatabase
import os

URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
USER = os.environ.get("NEO4J_USERNAME", "neo4j")
PASS = os.environ.get("NEO4J_PASSWORD", "neo4j123")

QUERIES = [
    ("Total nodes",            "MATCH (n) RETURN count(n) AS cnt"),
    ("Drug nodes",             "MATCH (n:Drug) RETURN count(n) AS cnt"),
    ("Chunk nodes",            "MATCH (n:Chunk) RETURN count(n) AS cnt"),
    ("Total relationships",    "MATCH ()-[r]->() RETURN count(r) AS cnt"),
    ("INTERACTS_WITH rels",    "MATCH ()-[r:INTERACTS_WITH]->() RETURN count(r) AS cnt"),
    ("HAS_CHUNK rels",         "MATCH ()-[r:HAS_CHUNK]->() RETURN count(r) AS cnt"),
    ("NEXT_CHUNK rels",        "MATCH ()-[r:NEXT_CHUNK]->() RETURN count(r) AS cnt"),
    ("Chunks with embeddings", "MATCH (c:Chunk) WHERE c.embedding IS NOT NULL RETURN count(c) AS cnt"),
]

def main():
    driver = GraphDatabase.driver(URI, auth=(USER, PASS))
    print(f"\n{'='*50}")
    print(f"  Neo4j Ingestion Progress  ({URI})")
    print(f"{'='*50}\n")
    with driver.session() as session:
        for label, query in QUERIES:
            try:
                result = session.run(query).single()
                count = result["cnt"] if result else 0
                print(f"  {label:<30} {count:>8,}")
            except Exception as e:
                print(f"  {label:<30} ERROR: {e}")

        # Show sample drugs
        print(f"\n{'─'*50}")
        print("  Sample Drug names (first 10):")
        print(f"{'─'*50}")
        try:
            results = session.run("MATCH (d:Drug) RETURN d.name AS name ORDER BY d.name LIMIT 10")
            for i, rec in enumerate(results, 1):
                print(f"    {i}. {rec['name']}")
        except Exception as e:
            print(f"    ERROR: {e}")

        # Show sample interactions
        print(f"\n{'─'*50}")
        print("  Sample Interactions (first 5):")
        print(f"{'─'*50}")
        try:
            results = session.run(
                "MATCH (a:Drug)-[r:INTERACTS_WITH]->(b:Drug) "
                "RETURN a.name AS drug1, r.interaction_type AS type, b.name AS drug2 LIMIT 5"
            )
            for i, rec in enumerate(results, 1):
                print(f"    {i}. {rec['drug1']} --[{rec['type']}]--> {rec['drug2']}")
        except Exception as e:
            print(f"    ERROR: {e}")

    driver.close()
    print(f"\n{'='*50}\n")

if __name__ == "__main__":
    main()
