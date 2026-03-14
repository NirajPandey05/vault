"""Factory for creating database provider instances."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import DatabaseProvider


def get_database_provider(provider_type: str | None = None) -> "DatabaseProvider":
    """
    Get database provider instance based on configuration.

    Args:
        provider_type: Specific provider to use, or None for config default
            Options: 'supabase', 'postgres', 'sqlite'

    Returns:
        Configured database provider instance

    Raises:
        ValueError: If provider_type is unknown
        ImportError: If required dependencies are missing
    """
    # Import here to avoid circular imports
    from ..config import get_config

    config = get_config()
    provider_type = provider_type or config.database_provider

    if provider_type == "supabase":
        from .supabase_provider import SupabaseProvider

        if not config.supabase_url or not config.supabase_key:
            raise ValueError(
                "Supabase requires SUPABASE_URL and SUPABASE_KEY in config/environment"
            )

        return SupabaseProvider(url=config.supabase_url, key=config.supabase_key)

    elif provider_type == "postgres":
        from .postgres_provider import PostgresProvider

        if not config.postgres_connection_string:
            raise ValueError(
                "PostgreSQL requires POSTGRES_CONNECTION_STRING in config/environment"
            )

        return PostgresProvider(connection_string=config.postgres_connection_string)

    elif provider_type == "sqlite":
        from .sqlite_provider import SQLiteProvider

        db_path = str(config.sqlite_db_path)
        return SQLiteProvider(db_path=db_path)

    else:
        raise ValueError(
            f"Unknown database provider: {provider_type}. "
            f"Choose from: 'supabase', 'postgres', 'sqlite'"
        )


def list_available_providers() -> dict[str, dict]:
    """
    List available database providers with metadata.

    Returns:
        Dict mapping provider name to metadata (description, requirements, etc.)
    """
    return {
        "supabase": {
            "name": "Supabase",
            "description": "Managed PostgreSQL with pgvector (cloud)",
            "requirements": ["supabase"],
            "config_keys": ["SUPABASE_URL", "SUPABASE_KEY"],
            "use_case": "Cloud, multi-device sync, free tier available",
            "cost": "$0/mo (free tier)",
        },
        "postgres": {
            "name": "PostgreSQL",
            "description": "Direct PostgreSQL connection with pgvector",
            "requirements": ["psycopg2-binary", "pgvector"],
            "config_keys": ["POSTGRES_CONNECTION_STRING"],
            "use_case": "Self-hosted, Neon, Railway, Render, etc.",
            "cost": "Varies by hosting (free options available)",
        },
        "sqlite": {
            "name": "SQLite",
            "description": "Local SQLite database with numpy-based vector search",
            "requirements": ["numpy"],
            "config_keys": ["SQLITE_DB_PATH"],
            "use_case": "Local/offline, single device, prototyping",
            "cost": "$0 (local file)",
        },
    }
