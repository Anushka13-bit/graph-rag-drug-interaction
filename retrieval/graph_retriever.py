"""Graph-based retrieval for DDI reasoning."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from langchain_core.language_models.chat_models import BaseChatModel

from graph.graph_queries import (
    GET_DRUG_CONTEXT_CHUNKS,
    GET_DRUG_INTERACTIONS,
    GET_MULTI_HOP_INTERACTIONS,
    GET_NEIGHBORHOOD,
    LIST_DRUG_NAMES,
)
from graph.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


@dataclass
class GraphContext:
    direct_interactions: List[Dict[str, object]] = field(default_factory=list)
    multi_hop_paths: List[Dict[str, object]] = field(default_factory=list)
    neighborhood: List[Dict[str, object]] = field(default_factory=list)
    supporting_chunks: List[Dict[str, object]] = field(default_factory=list)


class GraphRetriever:
    """Cypher-backed retrieval around detected drug entities."""

    def __init__(self, client: Neo4jClient, llm: Optional[BaseChatModel] = None) -> None:
        self.client = client
        self.llm = llm

    def _known_drugs(self) -> List[str]:
        try:
            rows = self.client.execute_query(LIST_DRUG_NAMES, {})
            if rows and rows[0].get("names"):
                return list(rows[0]["names"])
        except Exception as e:
            logger.warning("Could not list drugs: %s", e)
        return []

    def extract_drug_names_from_query(self, query: str) -> List[str]:
        """Match query tokens against known Drug nodes; optional LLM fallback."""
        known = self._known_drugs()
        if not known:
            return self._llm_drug_extract(query)
        lowered = query.lower()
        found: List[str] = []
        for name in known:
            if not name:
                continue
            pattern = re.compile(r"\b" + re.escape(name.lower()) + r"\b")
            if pattern.search(lowered):
                found.append(name)
        if found:
            return sorted(set(found))
        return self._llm_drug_extract(query)

    def _llm_drug_extract(self, query: str) -> List[str]:
        if self.llm is None:
            return []
        try:
            from langchain_core.output_parsers import PydanticOutputParser
            from langchain_core.prompts import ChatPromptTemplate
            from pydantic import BaseModel, Field

            class DrugNames(BaseModel):
                names: List[str] = Field(default_factory=list)

            parser = PydanticOutputParser(pydantic_object=DrugNames)
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "Extract drug names mentioned in the user question. JSON only.\n"
                        "{format_instructions}",
                    ),
                    ("human", "{q}"),
                ]
            ).partial(format_instructions=parser.get_format_instructions())
            chain = prompt | self.llm | parser
            out: DrugNames = chain.invoke({"q": query})
            return [n.strip() for n in out.names if n.strip()]
        except Exception as e:
            logger.warning("LLM drug extraction failed: %s", e)
            return []

    def retrieve(self, query: str, drug_names: List[str]) -> GraphContext:
        """Collect interactions, paths, neighborhoods, and supporting chunks."""
        ctx = GraphContext()
        if not drug_names:
            drug_names = self.extract_drug_names_from_query(query)
        for d in drug_names:
            try:
                ctx.direct_interactions.extend(
                    self.client.execute_query(GET_DRUG_INTERACTIONS, {"drug_name": d, "limit": 20})
                )
                ctx.neighborhood.extend(
                    self.client.execute_query(GET_NEIGHBORHOOD, {"drug_name": d, "limit": 20})
                )
                ctx.supporting_chunks.extend(
                    self.client.execute_query(GET_DRUG_CONTEXT_CHUNKS, {"drug_name": d, "limit": 10})
                )
            except Exception as e:
                logger.error("Graph retrieve failed for %s: %s", d, e)
        if len(drug_names) >= 2:
            d1, d2 = drug_names[0], drug_names[1]
            try:
                ctx.multi_hop_paths.extend(
                    self.client.execute_query(
                        GET_MULTI_HOP_INTERACTIONS,
                        {"drug1": d1, "drug2": d2, "limit": 10},
                    )
                )
            except Exception as e:
                logger.debug("multi-hop query failed: %s", e)
        return ctx
