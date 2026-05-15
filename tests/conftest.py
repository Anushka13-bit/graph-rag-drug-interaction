"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from config.settings import Settings


@pytest.fixture()
def test_settings() -> Settings:
    return Settings(
        neo4j_uri="bolt://localhost:7687",
        neo4j_username="neo4j",
        neo4j_password="pass",
        neo4j_database="neo4j",
        use_openai=False,
        embedding_dimension=384,
    )
