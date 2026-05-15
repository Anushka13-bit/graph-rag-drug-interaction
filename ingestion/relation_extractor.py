"""Relation extraction from DDICorpus pairs or LLM for unstructured text."""

from __future__ import annotations

from typing import List, Optional

from langchain_core.documents import Document
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ingestion.xml_parser import DDISentence, Entity, Pair, parse_ddi_xml_file


class ExtractedRelation(BaseModel):
    subject: str
    predicate: str
    object: str
    interaction_type: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_text: str


class RelationList(BaseModel):
    relations: List[ExtractedRelation] = Field(default_factory=list)


def _entity_map(sentence: DDISentence) -> dict[str, Entity]:
    return {e.entity_id: e for e in sentence.entities}


def _ddi_type_to_predicate(interaction_type: Optional[str]) -> str:
    if not interaction_type:
        return "INTERACTS_WITH"
    t = interaction_type.lower()
    if t == "effect":
        return "INTERACTS_WITH_EFFECT"
    if t == "mechanism":
        return "INTERACTS_WITH_MECHANISM"
    if t == "advise":
        return "INTERACTS_WITH_ADVISE"
    if t == "int":
        return "INTERACTS_WITH"
    return "INTERACTS_WITH"


def relations_from_ddi_sentence(sentence: DDISentence) -> List[ExtractedRelation]:
    """High-confidence relations from annotated pairs."""
    em = _entity_map(sentence)
    rels: List[ExtractedRelation] = []
    for p in sentence.pairs:
        if not p.ddi:
            continue
        e1 = em.get(p.e1_id)
        e2 = em.get(p.e2_id)
        if not e1 or not e2 or not e1.text or not e2.text:
            continue
        rels.append(
            ExtractedRelation(
                subject=e1.text.strip(),
                predicate=_ddi_type_to_predicate(p.interaction_type),
                object=e2.text.strip(),
                interaction_type=p.interaction_type,
                confidence=1.0,
                evidence_text=sentence.text,
            )
        )
    return rels


def relations_from_ddi_xml_path(path: str) -> List[ExtractedRelation]:
    """Parse a single XML file and collect all DDI relations."""
    out: List[ExtractedRelation] = []
    for sent in parse_ddi_xml_file(path):
        out.extend(relations_from_ddi_sentence(sent))
    return out


def extract_relations_from_text_llm(text: str, llm: BaseChatModel) -> List[ExtractedRelation]:
    """LLM relation extraction for PDF-derived text."""
    parser = PydanticOutputParser(pydantic_object=RelationList)
    fmt = parser.get_format_instructions()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Extract drug-drug and drug-disease relations from the passage. "
                "Use predicates among: INTERACTS_WITH, CAUSES, TREATS, INHIBITS, INDUCES. "
                "Return JSON only per schema.\n"
                "{format_instructions}",
            ),
            ("human", "{text}"),
        ]
    ).partial(format_instructions=fmt)
    chain = prompt | llm | parser
    result: RelationList = chain.invoke({"text": text})
    return result.relations


def relations_for_pdf_chunk(doc: Document, llm: BaseChatModel) -> List[ExtractedRelation]:
    """Extract relations for a single PDF chunk."""
    return extract_relations_from_text_llm(doc.page_content, llm)
