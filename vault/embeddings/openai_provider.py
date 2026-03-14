"""OpenAI embedding provider."""

from typing import List

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from . import EmbeddingProvider


class OpenAIProvider(EmbeddingProvider):
    """OpenAI embeddings provider (text-embedding-3-small/large)."""

    def __init__(
        self,
        model_name: str = "openai-small",
        api_key: str | None = None,
        model_id: str = "text-embedding-3-small",
        dimensions: int = 1536,
    ):
        if OpenAI is None:
            raise ImportError("openai package not installed. Run: pip install openai")

        super().__init__(model_name=model_name, dimensions=dimensions)
        self.client = OpenAI(api_key=api_key)
        self.model_id = model_id

    def embed(self, text: str) -> List[float]:
        """Generate embedding for single text using OpenAI."""
        try:
            response = self.client.embeddings.create(
                model=self.model_id,
                input=text,
                dimensions=self.dimensions,
            )
            embedding = response.data[0].embedding
            return self.normalize_vector(embedding)

        except Exception as e:
            raise RuntimeError(f"OpenAI embedding failed: {e}")

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts (efficient batch API)."""
        try:
            response = self.client.embeddings.create(
                model=self.model_id,
                input=texts,
                dimensions=self.dimensions,
            )
            embeddings = [item.embedding for item in response.data]
            return [self.normalize_vector(emb) for emb in embeddings]

        except Exception as e:
            raise RuntimeError(f"OpenAI batch embedding failed: {e}")
