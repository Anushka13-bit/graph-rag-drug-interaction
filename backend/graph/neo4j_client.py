"""Neo4j driver wrapper with pooling, retries, and health checks."""

from __future__ import annotations

import logging
from types import TracebackType
from typing import Any, List, Mapping, Optional, Type

from neo4j import GraphDatabase, Driver
from neo4j.exceptions import Neo4jError, ServiceUnavailable, TransientError

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Synchronous Neo4j client with context manager support."""

    def __init__(
        self,
        uri: str,
        username: str,
        password: str,
        database: str = "neo4j",
        max_connection_lifetime: int = 3600,
    ) -> None:
        self._uri = uri
        self._username = username
        self._password = password
        self.database = database
        self._driver: Optional[Driver] = GraphDatabase.driver(
            uri,
            auth=(username, password),
            max_connection_lifetime=max_connection_lifetime,
        )

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def __enter__(self) -> Neo4jClient:
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.close()

    @property
    def driver(self) -> Driver:
        if self._driver is None:
            raise RuntimeError("Neo4j driver is closed")
        return self._driver

    def health_check(self) -> bool:
        """Return True if a simple query succeeds."""
        try:
            self.execute_query("RETURN 1 AS ok", {})
            return True
        except Exception as e:
            logger.warning("Neo4j health check failed: %s", e)
            return False

    def execute_query(self, cypher: str, params: Mapping[str, Any]) -> List[Mapping[str, Any]]:
        """Run a read/write query and return records as dict-like mappings."""
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(cypher, dict(params))
                return [r.data() for r in result]
        except Neo4jError as e:
            logger.exception("Neo4j query failed: %s", e)
            raise

    def execute_write(self, cypher: str, params: Mapping[str, Any]) -> List[Mapping[str, Any]]:
        """Execute write transaction with retry on transient errors."""
        last_error: Optional[Exception] = None
        for attempt in range(3):
            try:

                def work(tx: Any) -> List[Mapping[str, Any]]:
                    result = tx.run(cypher, dict(params))
                    return [r.data() for r in result]

                with self.driver.session(database=self.database) as session:
                    return session.execute_write(work)
            except (TransientError, ServiceUnavailable) as e:
                last_error = e
                logger.warning("Transient Neo4j error (attempt %s): %s", attempt + 1, e)
            except Neo4jError as e:
                logger.exception("Neo4j write failed: %s", e)
                raise
        if last_error:
            raise last_error
        return []
