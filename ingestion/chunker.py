"""Chunk LangChain documents with overlap."""

from __future__ import annotations

from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import Settings


def chunk_documents(documents: List[Document], settings: Settings) -> List[Document]:
    """Split documents when longer than chunk_size; otherwise pass through with chunk metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    out: List[Document] = []
    for doc in documents:
        text = doc.page_content or ""
        meta = dict(doc.metadata)
        if len(text) < settings.chunk_size:
            meta["chunk_index"] = 0
            meta["total_chunks"] = 1
            sid = str(
                meta.get("sentence_id")
                or f"{meta.get('source', 'doc')}::p{meta.get('page_number', 0)}"
            )
            meta["chunk_id"] = f"{sid}::0"
            out.append(Document(page_content=text, metadata=meta))
            continue
        splits = splitter.split_documents([doc])
        total = len(splits)
        for i, chunk in enumerate(splits):
            m = dict(chunk.metadata)
            m["chunk_index"] = i
            m["total_chunks"] = total
            sid = str(
                m.get("sentence_id")
                or f"{m.get('source', 'doc')}::p{m.get('page_number', 0)}"
            )
            m["chunk_id"] = f"{sid}::{i}"
            out.append(Document(page_content=chunk.page_content, metadata=m))
    return out
