"""Configuration management for Vault."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database Configuration
    database_provider: Literal["supabase", "postgres", "sqlite"] = Field(
        default="supabase", description="Database backend to use"
    )

    # Supabase Configuration
    supabase_url: str | None = Field(default=None, description="Supabase project URL")
    supabase_key: str | None = Field(default=None, description="Supabase anon/service key")

    # PostgreSQL Configuration (for direct connections)
    postgres_connection_string: str | None = Field(
        default=None,
        description="PostgreSQL connection string (postgresql://user:pass@host:5432/dbname)",
    )

    # SQLite Configuration
    sqlite_db_path: Path = Field(
        default=Path.home() / ".vault" / "vault.db",
        description="Path to SQLite database file",
    )

    # Document Store Configuration
    vault_store_path: Path = Field(
        default=Path("vault_store"),
        description="Directory for linked documents (relative to working dir)",
    )

    # AWS Configuration
    aws_region: str = Field(default="us-east-1", description="AWS region for Bedrock")
    aws_profile: str = Field(default="default", description="AWS profile name")

    # OpenAI Configuration (optional)
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")

    # Google Configuration (optional)
    google_api_key: str | None = Field(default=None, description="Google Generative AI API key")

    # Embedding Configuration
    embedding_provider: Literal["bedrock-titan", "openai-small", "openai-large", "google-embed"] = Field(
        default="bedrock-titan", description="Active embedding provider"
    )
    embedding_dimension: int = Field(
        default=1536, description="Vector dimension (standardized)"
    )

    # Application Settings
    log_level: str = Field(default="INFO", description="Logging level")

    def get_model_config(self, model_name: str) -> dict:
        """Get configuration for a specific embedding model."""
        models = {
            "bedrock-titan": {
                "provider": "aws",
                "model_id": "amazon.titan-embed-text-v2:0",
                "dimensions": 1536,
                "cost_per_1k_tokens": 0.0002,
            },
            "openai-small": {
                "provider": "openai",
                "model_id": "text-embedding-3-small",
                "dimensions": 1536,
                "cost_per_1k_tokens": 0.00002,
            },
            "openai-large": {
                "provider": "openai",
                "model_id": "text-embedding-3-large",
                "dimensions": 3072,
                "cost_per_1k_tokens": 0.00013,
            },
            "google-embed": {
                "provider": "google",
                "model_id": "models/gemini-embedding-001",
                "dimensions": 3072,
                "cost_per_1k_tokens": 0.00001,
            },
        }
        return models.get(model_name, models["bedrock-titan"])


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get or create global config instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config() -> Config:
    """Force reload configuration from environment."""
    global _config
    _config = Config()
    return _config
