"""Load DDICorpus and PDFs into LangChain Documents."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from ingestion.xml_parser import DDISentence, Entity, parse_ddi_xml_file


def _entity_by_id(entities: List[Entity]) -> Dict[str, Entity]:
    return {e.entity_id: e for e in entities}


def _document_from_sentence(sent: DDISentence, source_file: str) -> Document:
    drugs: List[str] = []
    interaction_types: List[str] = []
    ddi_label = "false"
    ent_map = _entity_by_id(sent.entities)
    for p in sent.pairs:
        if p.ddi:
            ddi_label = "true"
            if p.interaction_type:
                interaction_types.append(p.interaction_type)
        e1 = ent_map.get(p.e1_id)
        e2 = ent_map.get(p.e2_id)
        for e in (e1, e2):
            if e and e.type.lower() == "drug" and e.text:
                drugs.append(e.text)
    drugs = sorted(set(drugs))
    itype: Optional[str] = interaction_types[0] if interaction_types else None
    meta: Dict[str, Any] = {
        "sentence_id": sent.sentence_id,
        "source_file": source_file,
        "drugs": drugs,
        "interaction_type": itype,
        "ddi_label": ddi_label,
    }
    return Document(page_content=sent.text, metadata=meta)


def load_ddi_corpus(data_dir: str) -> List[Document]:
    """Load all XML under data_dir into LangChain Documents (one per sentence)."""
    docs: List[Document] = []
    for root_dir, _dirs, files in os.walk(data_dir):
        for name in files:
            if not name.lower().endswith(".xml"):
                continue
            full = os.path.join(root_dir, name)
            for sent in parse_ddi_xml_file(full):
                docs.append(_document_from_sentence(sent, source_file=full))
    return docs


def load_pdfs(pdf_dir: str) -> List[Document]:
    """Load PDFs using PyPDFLoader."""
    out: List[Document] = []
    for root_dir, _dirs, files in os.walk(pdf_dir):
        for name in files:
            if not name.lower().endswith(".pdf"):
                continue
            path = os.path.join(root_dir, name)
            loader = PyPDFLoader(path)
            for doc in loader.load():
                meta = dict(doc.metadata)
                meta.setdefault("source", path)
                out.append(Document(page_content=doc.page_content, metadata=meta))
    return out
