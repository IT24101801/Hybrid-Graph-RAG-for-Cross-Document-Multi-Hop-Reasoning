from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application configuration.

    Values are loaded from environment variables and the .env file.
    """

    # Application
    app_name: str = "AshenGraph"
    app_env: str = "development"
    debug: bool = True

    # LLM
    openrouter_api_key: str = ""
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = ""

    # Embeddings
    voyage_api_key: str = ""
    embedding_model: str = "voyage-4-lite"

    # Chroma
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_name: str = "ashen_era_chunks"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = ""
    neo4j_database: str = "neo4j"

    # Data
    raw_data_dir: str = "./data/raw"
    processed_data_dir: str = "./data/processed"

    # Retrieval
    vector_top_k: int = 10
    graph_max_hops: int = 3
    final_evidence_top_k: int = 8

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def raw_data_path(self) -> Path:
        return Path(self.raw_data_dir)

    @property
    def processed_data_path(self) -> Path:
        return Path(self.processed_data_dir)

    @property
    def chroma_path(self) -> Path:
        return Path(self.chroma_persist_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()