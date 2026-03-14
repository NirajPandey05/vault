"""Model-agnostic embedding interface."""

from abc import ABC, abstractmethod
from typing import List


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    def __init__(self, model_name: str, dimensions: int = 1536):
        self.model_name = model_name
        self.dimensions = dimensions

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            Vector embedding as list of floats
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (more efficient).

        Args:
            texts: List of input texts

        Returns:
            List of vector embeddings
        """
        pass

    def normalize_vector(self, vector: List[float]) -> List[float]:
        """
        Normalize vector to target dimensions.

        Pads with zeros if too short, truncates if too long.
        """
        if len(vector) == self.dimensions:
            return vector
        elif len(vector) < self.dimensions:
            # Pad with zeros
            return vector + [0.0] * (self.dimensions - len(vector))
        else:
            # Truncate (rare case)
            return vector[: self.dimensions]
