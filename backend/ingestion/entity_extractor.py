"""Entity extraction: XML-grounded for DDICorpus; LLM NER for PDFs."""

from __future__ import annotations

import json
from typing import List, Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from langchain_core.documents import Document


class ExtractedEntity(BaseModel):
    name: str
    type: Literal["drug", "disease", "symptom", "mechanism", "gene"]
    aliases: List[str] = Field(default_factory=list)


class EntityList(BaseModel):
    entities: List[ExtractedEntity] = Field(default_factory=list)


def entities_from_ddi_metadata(doc: Document) -> List[ExtractedEntity]:
    """Use pre-annotated drug names from DDICorpus document metadata."""
    drugs = doc.metadata.get("drugs") or []
    return [
        ExtractedEntity(name=str(d), type="drug", aliases=[])
        for d in drugs
        if d
    ]


def extract_entities_from_pdf_text(
    text: str,
    llm: BaseChatModel,
) -> List[ExtractedEntity]:
    """LLM-based biomedical NER with structured JSON output."""
    parser = PydanticOutputParser(pydantic_object=EntityList)
    fmt = parser.get_format_instructions()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a biomedical NER system. Extract all drug names, diseases, "
                "biological mechanisms, and genes from the text. Return ONLY the JSON matching the schema.\n"
                "{format_instructions}",
            ),
            ("human", "{text}"),
        ]
    ).partial(format_instructions=fmt)
    chain = prompt | llm | parser
    result: EntityList = chain.invoke({"text": text})
    return result.entities


def serialize_entities(entities: List[ExtractedEntity]) -> str:
    """Serialize entities to JSON for storage or debugging."""
    return json.dumps([e.model_dump() for e in entities], ensure_ascii=False)
