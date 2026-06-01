"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import Any

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration for Neo4j, LLM, embeddings, and ingestion."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_username: str = Field(default="neo4j", alias="NEO4J_USERNAME")
    neo4j_password: str = Field(default="your_password", alias="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", alias="NEO4J_DATABASE")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    use_openai: bool = Field(default=False, alias="USE_OPENAI")

    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="mistral", alias="OLLAMA_MODEL")

    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL",
    )
    embedding_dimension: int = Field(default=384, alias="EMBEDDING_DIMENSION")
    # auto | ollama | huggingface — use ollama for nomic-embed-text, etc.
    embedding_backend: str = Field(default="auto", alias="EMBEDDING_BACKEND")

    neo4j_vector_index_name: str = Field(default="drug_chunks", alias="NEO4J_VECTOR_INDEX_NAME")
    chunk_size: int = Field(default=512, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=64, alias="CHUNK_OVERLAP")

    data_dir: str = Field(default="./data/raw/DDICorpusBrat 2", alias="DATA_DIR")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    def get_llm(self, **kwargs: Any) -> BaseChatModel:
        """Return ChatOpenAI or ChatOllama based on USE_OPENAI."""
        if self.use_openai:
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required when USE_OPENAI=true")
            return ChatOpenAI(
                model=kwargs.pop("model", "gpt-4o"),
                api_key=self.openai_api_key,
                **kwargs,
            )
        return ChatOllama(
            base_url=self.ollama_base_url,
            model=kwargs.pop("model", self.ollama_model),
            **kwargs,
        )

    def get_embeddings(self, **kwargs: Any) -> Embeddings:
        """Return embeddings matching the configured backend (OpenAI / Ollama / HuggingFace)."""
        if self.use_openai:
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required when USE_OPENAI=true")
            return OpenAIEmbeddings(
                model=kwargs.pop("model", "text-embedding-3-small"),
                api_key=self.openai_api_key,
                **kwargs,
            )
        from embeddings.embedder import resolve_embedding_backend

        if resolve_embedding_backend(self) == "ollama":
            from langchain_ollama import OllamaEmbeddings

            return OllamaEmbeddings(
                model=kwargs.pop("model", self.embedding_model),
                base_url=kwargs.pop("base_url", self.ollama_base_url),
            )
        return HuggingFaceEmbeddings(
            model_name=kwargs.pop("model_name", self.embedding_model),
            **kwargs,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings singleton for import-time access."""
    return Settings()
