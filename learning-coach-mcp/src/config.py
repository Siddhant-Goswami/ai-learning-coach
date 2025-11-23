"""Configuration management for AI Learning Coach."""

import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SupabaseConfig(BaseModel):
    """Supabase configuration."""

    url: str = Field(..., env="SUPABASE_URL")
    key: str = Field(..., env="SUPABASE_KEY")
    service_key: Optional[str] = Field(None, env="SUPABASE_SERVICE_KEY")


class OpenAIConfig(BaseModel):
    """OpenAI configuration."""

    api_key: str = Field(..., env="OPENAI_API_KEY")
    embedding_model: str = Field(default="text-embedding-3-small")
    embedding_dimensions: int = Field(default=1536)


class AnthropicConfig(BaseModel):
    """Anthropic configuration."""

    api_key: str = Field(..., env="ANTHROPIC_API_KEY")
    model: str = Field(default="claude-sonnet-4-5-20250929")


class BootcampConfig(BaseModel):
    """100xEngineers bootcamp API configuration."""

    api_url: Optional[str] = Field(None, env="BOOTCAMP_API_URL")
    api_key: Optional[str] = Field(None, env="BOOTCAMP_API_KEY")


class RAGConfig(BaseModel):
    """RAG pipeline configuration."""

    top_k_retrieval: int = Field(default=15)
    similarity_threshold: float = Field(default=0.70)
    chunk_size: int = Field(default=750)
    chunk_overlap: int = Field(default=100)


class RAGASConfig(BaseModel):
    """RAGAS evaluation configuration."""

    min_score: float = Field(default=0.70)
    max_retries: int = Field(default=2)


class IngestionConfig(BaseModel):
    """Content ingestion configuration."""

    interval_hours: int = Field(default=6)
    max_concurrent_fetches: int = Field(default=5)


class CacheConfig(BaseModel):
    """Cache configuration."""

    digest_cache_hours: int = Field(default=6)


class AppConfig(BaseModel):
    """Main application configuration."""

    environment: str = Field(default="development", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    default_user_id: str = Field(
        default="00000000-0000-0000-0000-000000000001", env="DEFAULT_USER_ID"
    )

    supabase: SupabaseConfig
    openai: OpenAIConfig
    anthropic: AnthropicConfig
    bootcamp: BootcampConfig
    rag: RAGConfig
    ragas: RAGASConfig
    ingestion: IngestionConfig
    cache: CacheConfig


def load_config() -> AppConfig:
    """Load and validate configuration from environment variables."""
    return AppConfig(
        supabase=SupabaseConfig(
            url=os.getenv("SUPABASE_URL", ""),
            key=os.getenv("SUPABASE_KEY", ""),
            service_key=os.getenv("SUPABASE_SERVICE_KEY"),
        ),
        openai=OpenAIConfig(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
            embedding_dimensions=int(os.getenv("EMBEDDING_DIMENSIONS", "1536")),
        ),
        anthropic=AnthropicConfig(
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        ),
        bootcamp=BootcampConfig(
            api_url=os.getenv("BOOTCAMP_API_URL"),
            api_key=os.getenv("BOOTCAMP_API_KEY"),
        ),
        rag=RAGConfig(
            top_k_retrieval=int(os.getenv("TOP_K_RETRIEVAL", "15")),
            similarity_threshold=float(os.getenv("SIMILARITY_THRESHOLD", "0.70")),
        ),
        ragas=RAGASConfig(
            min_score=float(os.getenv("RAGAS_MIN_SCORE", "0.70")),
            max_retries=int(os.getenv("RAGAS_MAX_RETRIES", "2")),
        ),
        ingestion=IngestionConfig(
            interval_hours=int(os.getenv("INGESTION_INTERVAL_HOURS", "6")),
        ),
        cache=CacheConfig(
            digest_cache_hours=int(os.getenv("DIGEST_CACHE_HOURS", "6")),
        ),
    )


# Global config instance
config = load_config()
