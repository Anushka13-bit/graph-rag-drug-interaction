"""Tests for entity extraction helpers."""

from __future__ import annotations

from typing import Any, Iterator, List, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from ingestion.entity_extractor import entities_from_ddi_metadata, extract_entities_from_pdf_text
from langchain_core.documents import Document


class _FakeLLM(BaseChatModel):
    content: str = ""

    @property
    def _llm_type(self) -> str:
        return "fake"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=self.content))])

    def bind_tools(self, *args: Any, **kwargs: Any) -> BaseChatModel:
        return self

    def stream(self, *args: Any, **kwargs: Any) -> Iterator[ChatGeneration]:
        yield ChatGeneration(message=AIMessage(content=self.content))


def test_entities_from_ddi_metadata() -> None:
    doc = Document(page_content="x", metadata={"drugs": ["aspirin"]})
    ents = entities_from_ddi_metadata(doc)
    assert ents[0].name == "aspirin"
    assert ents[0].type == "drug"


def test_extract_entities_from_pdf_text_parses_json() -> None:
    payload = '{"entities": [{"name": "metformin", "type": "drug", "aliases": []}]}'
    llm = _FakeLLM(content=payload)
    out = extract_entities_from_pdf_text("Patient on metformin.", llm)
    assert out[0].name == "metformin"
