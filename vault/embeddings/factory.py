"""Factory for creating embedding providers."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import EmbeddingProvider

from ..config import get_config


def get_embedding_provider(provider_name: str | None = None) -> "EmbeddingProvider":
    """
    Get embedding provider instance based on configuration.

    Args:
        provider_name: Specific provider to use, or None for config default

    Returns:
        Configured embedding provider instance
    """
    from .bedrock import BedrockTitanProvider
    from .openai_provider import OpenAIProvider
    from .google_provider import GoogleEmbeddingProvider

    config = get_config()
    provider_name = provider_name or config.embedding_provider

    if provider_name == "bedrock-titan":
        return BedrockTitanProvider(
            model_name=provider_name,
            dimensions=config.embedding_dimension,
            region=config.aws_region,
            profile=config.aws_profile,
        )
    elif provider_name == "openai-small":
        return OpenAIProvider(
            model_name=provider_name,
            api_key=config.openai_api_key,
            model_id="text-embedding-3-small",
            dimensions=1536,
        )
    elif provider_name == "openai-large":
        return OpenAIProvider(
            model_name=provider_name,
            api_key=config.openai_api_key,
            model_id="text-embedding-3-large",
            dimensions=1536,  # Can go up to 3072, but we standardize
        )
    elif provider_name == "google-embed":
        return GoogleEmbeddingProvider(
            model_name=provider_name,
            api_key=config.google_api_key,
            model_id="models/gemini-embedding-001",
            dimensions=3072,
        )
    else:
        raise ValueError(f"Unknown embedding provider: {provider_name}")
