"""Google Generative AI embedding provider (uses google-genai SDK)."""

from typing import List

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = None
    genai_types = None

from . import EmbeddingProvider


class GoogleEmbeddingProvider(EmbeddingProvider):
    """Google Generative AI embeddings provider using the google-genai SDK."""

    def __init__(
        self,
        model_name: str = "google-embed",
        api_key: str | None = None,
        model_id: str = "models/gemini-embedding-001",
        dimensions: int = 3072,
    ):
        if genai is None:
            raise ImportError(
                "google-genai package not installed. Run: pip install google-genai"
            )

        if not api_key:
            raise ValueError("GOOGLE_API_KEY is required for Google embeddings")

        super().__init__(model_name=model_name, dimensions=dimensions)
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id

    def embed(self, text: str) -> List[float]:
        """Generate embedding for single text using Google Generative AI."""
        try:
            response = self.client.models.embed_content(
                model=self.model_id,
                contents=text,
            )
            embedding = response.embeddings[0].values
            return self.normalize_vector(list(embedding))

        except Exception as e:
            raise RuntimeError(f"Google embedding failed: {e}")

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            response = self.client.models.embed_content(
                model=self.model_id,
                contents=texts,
            )
            return [self.normalize_vector(list(emb.values)) for emb in response.embeddings]

        except Exception as e:
            raise RuntimeError(f"Google batch embedding failed: {e}")
