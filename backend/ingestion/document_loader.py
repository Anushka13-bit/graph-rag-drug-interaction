"""Load DDICorpus (Brat or XML) and PDFs into LangChain Documents."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from ingestion.brat_parser import is_brat_corpus, parse_brat_corpus
from ingestion.xml_parser import DDISentence, Entity, parse_ddi_xml_file


def _entity_by_id(entities: List[Entity]) -> Dict[str, Entity]:
    return {e.entity_id: e for e in entities}


def _drug_names_from_sentence(sent: DDISentence) -> List[str]:
    """Collect drug/brand mention strings from entities and DDI pairs."""
    from ingestion.brat_parser import _DRUG_ENTITY_TYPES

    drugs: List[str] = []
    ent_map = _entity_by_id(sent.entities)
    for ent in sent.entities:
        if ent.type.upper() in _DRUG_ENTITY_TYPES or ent.type.lower() in ("drug", "brand"):
            if ent.text:
                drugs.append(ent.text)
    for p in sent.pairs:
        if not p.ddi:
            continue
        for eid in (p.e1_id, p.e2_id):
            e = ent_map.get(eid)
            if e and e.text:
                drugs.append(e.text)
    return sorted(set(drugs))


def _document_from_sentence(sent: DDISentence, source_file: str, split: str = "") -> Document:
    interaction_types: List[str] = []
    ddi_label = "false"
    for p in sent.pairs:
        if p.ddi:
            ddi_label = "true"
            if p.interaction_type:
                interaction_types.append(p.interaction_type)
    itype: Optional[str] = interaction_types[0] if interaction_types else None
    meta: Dict[str, Any] = {
        "sentence_id": sent.sentence_id,
        "source_file": source_file,
        "split": split,
        "drugs": _drug_names_from_sentence(sent),
        "interaction_type": itype,
        "ddi_label": ddi_label,
        "format": "brat",
    }
    return Document(page_content=sent.text, metadata=meta)


def load_ddi_brat_corpus(data_dir: str) -> List[Document]:
    """Load Brat Train+Test combined corpus (one Document per .txt passage)."""
    docs: List[Document] = []
    for sent in parse_brat_corpus(data_dir):
        src = sent.source_file or os.path.abspath(data_dir)
        docs.append(_document_from_sentence(sent, source_file=src, split=sent.split))
    return docs


def load_ddi_xml_corpus(data_dir: str) -> List[Document]:
    """Load legacy DDICorpus XML files."""
    docs: List[Document] = []
    for root_dir, _dirs, files in os.walk(data_dir):
        for name in files:
            if not name.lower().endswith(".xml"):
                continue
            full = os.path.join(root_dir, name)
            for sent in parse_ddi_xml_file(full):
                meta_doc = _document_from_sentence(sent, source_file=full, split="")
                meta_doc.metadata["format"] = "xml"
                docs.append(meta_doc)
    return docs


def load_ddi_corpus(data_dir: str) -> List[Document]:
    """Auto-detect Brat vs XML and load all annotated passages."""
    if is_brat_corpus(data_dir):
        return load_ddi_brat_corpus(data_dir)
    return load_ddi_xml_corpus(data_dir)


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
