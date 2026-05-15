# Biomedical Hybrid Graph-RAG (DDI)

Production-oriented hybrid **Graph-RAG** stack for **drug–drug interaction (DDI)** reasoning: **LangChain** orchestration, **Neo4j** for the knowledge graph and primary **vector index**, **FAISS** as optional fallback, and **FastAPI** for serving.

## Architecture (ASCII)

```
                    +------------------+
                    |   FastAPI API   |
                    +--------+---------+
                             |
              +--------------+---------------+
              |                              |
     +--------v---------+           +--------v---------+
     | HybridRetriever  |           |  GraphRAGChain |
     | vector + graph   |           |  LCEL prompt   |
     +--------+---------+           +--------+---------+
              |                              |
    +---------v----------+          +--------v---------+
    | VectorRetriever    |          | ChatOllama /     |
    | Neo4jVectorStore   |          | ChatOpenAI      |
    |  -> FAISS fallback |          +-----------------+
    +---------+----------+
              |
    +---------v---------+       +---------------------+
    | Neo4j (Bolt)      |       | SentenceTransformers |
    | Chunk + embedding|       | or OpenAI embeddings |
    | Drug, INTERACTS..|       +---------------------+
    +-------------------+
```

## Prerequisites

- **Docker** and **Docker Compose** (for Neo4j + optional app container)
- **Python 3.11+** (3.11 recommended; 3.12+ generally works)
- **Ollama** running locally when `USE_OPENAI=false` (e.g. `mistral` or `llama3`)
- **DDICorpus** XML files placed under `data/raw/` (see [DDICorpus](https://github.com/isegura/DDICorpus))

## Quick setup

1. **Clone / enter project**

```bash
cd biomedical-graphrag
```

2. **Environment**

```bash
cp .env.example .env
# Edit .env: set NEO4J_PASSWORD to match docker-compose (default neo4j/your_password)
```

3. **Start Neo4j**

```bash
docker compose up -d neo4j
```

4. **Python virtualenv**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

5. **Neo4j schema + vector index**

```bash
python scripts/setup_neo4j_schema.py
```

6. **Ingest DDICorpus** (XML under `./data/raw/DDICorpus` or pass `--data-dir`)

```bash
python scripts/ingest_ddicopus.py --data-dir ./data/raw/DDICorpus
```

7. **Run API**

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Full stack via Compose

From the project directory (with `.env` present):

```bash
docker compose up -d
```

The `app` service builds the `Dockerfile` and runs Uvicorn on port **8000**.

## Example API calls (`curl`)

**Health**

```bash
curl -s http://localhost:8000/health
```

**Query (non-streaming)**

```bash
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"What happens if a patient takes warfarin and omeprazole together?","top_k":5,"include_graph_paths":true,"stream":false}'
```

**Query (streaming)**

```bash
curl -N -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"Explain DDI between aspirin and ibuprofen.","stream":true}'
```

**Trigger ingestion**

```bash
curl -s -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"data_type":"ddicopus","path":"./data/raw/DDICorpus"}'
```

**Ingestion status**

```bash
curl -s http://localhost:8000/ingest/status
```

**Graph neighborhood**

```bash
curl -s "http://localhost:8000/graph/entity/warfarin"
```

## Adding PDF documents

1. Put PDFs in a directory, e.g. `./data/raw/papers/`.
2. Run:

```bash
python scripts/ingest_pdfs.py --pdf-dir ./data/raw/papers
```

Or via API:

```bash
curl -s -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"data_type":"pdf","path":"./data/raw/papers"}'
```

PDF ingestion uses LLM-based NER and relation extraction (`USE_OPENAI` must allow access to your configured model).

## Switching Ollama vs OpenAI

In `.env`:

- **Local stack (default)**  
  - `USE_OPENAI=false`  
  - `OLLAMA_BASE_URL` / `OLLAMA_MODEL`  
  - `EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2`  
  - `EMBEDDING_DIMENSION=384` (must match the model and Neo4j vector index)

- **OpenAI**  
  - `USE_OPENAI=true`  
  - `OPENAI_API_KEY=sk-...`  
  - For embeddings, set `EMBEDDING_DIMENSION` to match your OpenAI embedding size (e.g. `1536` for `text-embedding-3-small` unless using a reduced dimension).  
  - Re-run `python scripts/setup_neo4j_schema.py` after changing embedding dimension so the Neo4j vector index matches.

## CLI query loop

```bash
python scripts/query_cli.py
```

## Tests

```bash
pytest
```

## Notes

- **Neo4j Bloom** is not bundled; use Neo4j Browser (`http://localhost:7474`) or Bloom against the same database.
- **Vector search** uses `CALL db.index.vector.queryNodes(...)`. If vector search errors at runtime, the retriever falls back to **FAISS** (requires a prior successful `build_index` during ingestion).
- **DDICorpus** licensing and redistribution follow the upstream repository; raw XML is ignored by `.gitignore` patterns under `data/raw/`.
