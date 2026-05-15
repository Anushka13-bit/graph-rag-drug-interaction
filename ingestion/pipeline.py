"""Orchestrate ingestion into Neo4j and vector indexes."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

from langchain_core.documents import Document

from config.settings import Settings, get_settings
from embeddings.embedder import get_embedder
from embeddings.faiss_store import build_index
from embeddings.neo4j_vector_store import Neo4jVectorStore
from graph import graph_builder as gb
from graph.neo4j_client import Neo4jClient
from ingestion.chunker import chunk_documents
from ingestion.document_loader import load_ddi_corpus, load_pdfs
from ingestion.entity_extractor import extract_entities_from_pdf_text
from ingestion.relation_extractor import (
    ExtractedRelation,
    relations_for_pdf_chunk,
    relations_from_ddi_sentence,
)
from ingestion.xml_parser import parse_ddi_xml_file
from reasoning.llm_client import get_chat_model


@dataclass
class IngestionStats:
    documents_processed: int = 0
    entities_created: int = 0
    relations_created: int = 0
    chunks_indexed: int = 0


class IngestionPipeline:
    """High-level ingestion for DDICorpus XML and PDFs."""

    def __init__(self, client: Neo4jClient, settings: Settings | None = None) -> None:
        self.client = client
        self.settings = settings or get_settings()
        self.embedder = get_embedder(self.settings)
        self.vector = Neo4jVectorStore(
            client,
            index_name=self.settings.neo4j_vector_index_name,
            dimensions=self.settings.embedding_dimension,
        )

    def run_ddicopus(self, data_dir: str) -> IngestionStats:
        """Parse DDICorpus XML, build graph, embed chunks, and index vectors."""
        stats = IngestionStats()
        self.vector.ensure_vector_index()
        all_relations: List[ExtractedRelation] = []
        drug_names: List[str] = []
        for root, _dirs, files in os.walk(data_dir):
            for name in files:
                if not name.lower().endswith(".xml"):
                    continue
                path = os.path.join(root, name)
                for sent in parse_ddi_xml_file(path):
                    rels = relations_from_ddi_sentence(sent)
                    all_relations.extend(rels)
                    for r in rels:
                        drug_names.extend([r.subject, r.object])
        gb.batch_upsert_drugs(self.client, drug_names)
        gb.batch_upsert_relations(self.client, all_relations)
        stats.relations_created = len(all_relations)
        stats.entities_created = len(set(drug_names))

        docs = load_ddi_corpus(data_dir)
        stats.documents_processed = len(docs)
        chunks = chunk_documents(docs, self.settings)
        texts = [c.page_content for c in chunks]
        embeddings = self.embedder.embed_batch(texts) if texts else []
        rows: list[dict] = []
        links: list[dict] = []
        for i, ch in enumerate(chunks):
            cid = str(ch.metadata.get("chunk_id") or f"{ch.metadata.get('sentence_id', 'unk')}::{i}")
            emb = embeddings[i] if i < len(embeddings) else None
            rows.append(
                {
                    "chunk_id": cid,
                    "text": ch.page_content,
                    "source": str(ch.metadata.get("source_file") or ch.metadata.get("sentence_id") or ""),
                    "page": ch.metadata.get("page"),
                    "chunk_index": ch.metadata.get("chunk_index", 0),
                    "embedding": emb,
                }
            )
            for drug in ch.metadata.get("drugs") or []:
                links.append({"drug": str(drug), "chunk_id": cid})
        gb.batch_upsert_chunks(self.client, rows)
        gb.batch_link_drugs_to_chunks(self.client, links)
        stats.chunks_indexed = len(rows)

        by_source: dict[str, list[str]] = {}
        for ch in chunks:
            cid = str(ch.metadata.get("chunk_id"))
            src = str(ch.metadata.get("source_file") or "")
            by_source.setdefault(src, []).append(cid)
        for src, ids in by_source.items():
            if len(ids) > 1:
                gb.link_sequential_chunks(self.client, ids, src)

        try:
            build_index(chunks, self.settings)
        except Exception:
            pass
        return stats

    def run_pdfs(self, pdf_dir: str) -> IngestionStats:
        """Ingest PDFs with LLM extraction (entities/relations) and indexing."""
        stats = IngestionStats()
        self.vector.ensure_vector_index()
        llm = get_chat_model(self.settings)
        docs = load_pdfs(pdf_dir)
        stats.documents_processed = len(docs)
        chunks = chunk_documents(docs, self.settings)
        relations: List[ExtractedRelation] = []
        drugs: List[str] = []
        chunk_drugs: list[list[str]] = []
        for ch in chunks:
            ents = extract_entities_from_pdf_text(ch.page_content, llm)
            dnames = [e.name for e in ents if e.type == "drug"]
            drugs.extend(dnames)
            chunk_drugs.append(dnames)
            relations.extend(relations_for_pdf_chunk(ch, llm))
        gb.batch_upsert_drugs(self.client, drugs)
        for r in relations:
            gb.upsert_relation(
                self.client,
                r.subject,
                r.predicate,
                r.object,
                {
                    "interaction_type": r.interaction_type,
                    "confidence": r.confidence,
                    "evidence_text": r.evidence_text,
                },
            )
        stats.relations_created = len(relations)
        stats.entities_created = len(set(drugs))

        texts = [c.page_content for c in chunks]
        embeddings = self.embedder.embed_batch(texts) if texts else []
        rows = []
        links = []
        for i, ch in enumerate(chunks):
            cid = str(ch.metadata.get("chunk_id") or f"pdf::{i}")
            emb = embeddings[i] if i < len(embeddings) else None
            rows.append(
                {
                    "chunk_id": cid,
                    "text": ch.page_content,
                    "source": str(ch.metadata.get("source") or ""),
                    "page": ch.metadata.get("page_number"),
                    "chunk_index": ch.metadata.get("chunk_index", 0),
                    "embedding": emb,
                }
            )
            for drug in chunk_drugs[i] if i < len(chunk_drugs) else []:
                links.append({"drug": drug, "chunk_id": cid})
        gb.batch_upsert_chunks(self.client, rows)
        gb.batch_link_drugs_to_chunks(self.client, links)
        stats.chunks_indexed = len(rows)
        try:
            build_index(chunks, self.settings)
        except Exception:
            pass
        return stats
