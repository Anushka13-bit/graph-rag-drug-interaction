"""Orchestrate ingestion into Neo4j and vector indexes."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from langchain_core.documents import Document

from config.settings import Settings, get_settings
from embeddings.embedder import get_embedder
from embeddings.faiss_store import build_index
from embeddings.neo4j_vector_store import Neo4jVectorStore
from graph import graph_builder as gb
from graph.neo4j_client import Neo4jClient
from ingestion.brat_parser import is_brat_corpus, parse_brat_corpus
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

logger = logging.getLogger(__name__)


@dataclass
class IngestionStats:
    documents_processed: int = 0
    entities_created: int = 0
    relations_created: int = 0
    chunks_indexed: int = 0
    train_documents: int = 0
    test_documents: int = 0


class IngestionPipeline:
    """High-level ingestion for DDICorpus (Brat Train+Test or XML) and PDFs."""

    def __init__(self, client: Neo4jClient, settings: Settings | None = None) -> None:
        self.client = client
        self.settings = settings or get_settings()
    
        
        print("Loading embedder...")
        self.embedder = get_embedder(self.settings)
        print("Embedder loaded.")
        self.vector = Neo4jVectorStore(
            client,
            index_name=self.settings.neo4j_vector_index_name,
            dimensions=self.settings.embedding_dimension,
        )

    def _collect_sentences(self, data_dir: str) -> list:
        """Parse Brat (Train+Test) or XML corpus into DDISentence list."""
        if is_brat_corpus(data_dir):
            sents = parse_brat_corpus(data_dir)
            logger.info(
                "Brat corpus: %s documents (Train+Test combined) from %s",
                len(sents),
                data_dir,
            )
            return sents
        import os

        sents = []
        for root, _dirs, files in os.walk(data_dir):
            for name in files:
                if not name.lower().endswith(".xml"):
                    continue
                path = os.path.join(root, name)
                sents.extend(parse_ddi_xml_file(path))
        return sents

    def run_ddicopus(self, data_dir: str) -> IngestionStats:
        stats = IngestionStats()

        print("1. Creating vector index")
        self.vector.ensure_vector_index()
        print("Done")

        print("2. Collecting sentences")
        print("Collecting corpus...")
        sentences = self._collect_sentences(data_dir)
        print(f"Collected {len(sentences)} sentences")
        sentences = self._collect_sentences(data_dir)
        print("Sentences:", len(sentences))

        print("3. Extracting relations")
        all_relations = []
        drug_names = []

        for sent in sentences:
            rels = relations_from_ddi_sentence(sent)
            all_relations.extend(rels)

            for r in rels:
                drug_names.extend([r.subject, r.object])

        print("Relations:", len(all_relations))
        print("Unique drugs:", len(set(drug_names)))

        print("4. Writing drugs")
        print("Creating drug nodes...")
        gb.batch_upsert_drugs(self.client, drug_names)
        print("Drug nodes done")
        print("Done")

        print("5. Writing relations")
        gb.batch_upsert_relations(self.client, all_relations)
        print("Done")

        print("6. Loading documents")
        docs = load_ddi_corpus(data_dir)
        print("Documents:", len(docs))

        print("7. Chunking")
        chunks = chunk_documents(docs, self.settings)
        print("Chunks:", len(chunks))

        texts = [c.page_content for c in chunks]

        print("8. Generating embeddings")
        embeddings = self.embedder.embed_batch(texts)
        print("Embeddings generated:", len(embeddings))

        rows = []
        links = []

        print("9. Preparing rows")

        for i, ch in enumerate(chunks):
            cid = str(ch.metadata.get("chunk_id") or i)

            rows.append(
                {
                    "chunk_id": cid,
                    "text": ch.page_content,
                    "source": str(ch.metadata.get("source_file") or ""),
                    "page": ch.metadata.get("page"),
                    "chunk_index": ch.metadata.get("chunk_index", 0),
                    "embedding": embeddings[i],
                }
            )

            for drug in ch.metadata.get("drugs") or []:
                links.append(
                    {
                        "drug": drug,
                        "chunk_id": cid,
                    }
                )

        print("Rows:", len(rows))
        print("Links:", len(links))

        print("10. Writing chunks")
        gb.batch_upsert_chunks(self.client, rows)
        print("Done")

        print("11. Linking chunks")
        gb.batch_link_drugs_to_chunks(self.client, links)
        print("Done")

        stats.documents_processed = len(docs)
        stats.entities_created = len(set(drug_names))
        stats.relations_created = len(all_relations)
        stats.chunks_indexed = len(rows)

        print("12. Building FAISS")

        try:
            build_index(chunks, self.settings)
        except Exception as e:
            print("FAISS skipped:", e)

        print("Finished")

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
