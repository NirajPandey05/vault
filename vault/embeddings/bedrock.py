"""AWS Bedrock Titan embedding provider."""

import json
from typing import List

import boto3

from . import EmbeddingProvider


class BedrockTitanProvider(EmbeddingProvider):
    """AWS Bedrock Titan Embeddings v2 provider."""

    SUPPORTED_REQUEST_DIMENSIONS = {256, 512, 1024}
    DEFAULT_REQUEST_DIMENSIONS = 1024

    def __init__(
        self,
        model_name: str = "bedrock-titan-v2",
        dimensions: int = 1536,
        region: str = "us-east-1",
        profile: str | None = None,
    ):
        super().__init__(model_name=model_name, dimensions=dimensions)

        # Initialize Bedrock client
        session_kwargs = {"region_name": region}
        if profile:
            session_kwargs["profile_name"] = profile

        session = boto3.Session(**session_kwargs)
        self.client = session.client("bedrock-runtime")
        self.model_id = "amazon.titan-embed-text-v2:0"
        self.request_dimensions = self._resolve_request_dimensions(dimensions)

    def _resolve_request_dimensions(self, target_dimensions: int) -> int:
        """Map the normalized output size to a Titan-supported request size."""
        if target_dimensions in self.SUPPORTED_REQUEST_DIMENSIONS:
            return target_dimensions
        return self.DEFAULT_REQUEST_DIMENSIONS

    @staticmethod
    def _extract_embedding(response_body: dict) -> List[float]:
        """Extract the float embedding from Bedrock's response payload."""
        embedding = response_body.get("embedding")
        if embedding:
            return embedding

        embeddings_by_type = response_body.get("embeddingsByType", {})
        if isinstance(embeddings_by_type, dict):
            float_embedding = embeddings_by_type.get("float")
            if float_embedding:
                return float_embedding

        return []

    def embed(self, text: str) -> List[float]:
        """Generate embedding for single text using Bedrock Titan."""
        try:
            request_body = {
                "inputText": text,
                "dimensions": self.request_dimensions,
                "normalize": True,
                "embeddingTypes": ["float"],
            }

            response = self.client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body),
            )

            response_body = json.loads(response["body"].read())
            embedding = self._extract_embedding(response_body)
            if not embedding:
                raise RuntimeError("Bedrock returned an empty float embedding.")

            return self.normalize_vector(embedding)

        except Exception as e:
            raise RuntimeError(
                "Bedrock embedding failed "
                f"for {self.model_id} with requested dimensions {self.request_dimensions}: {e}"
            )

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Note: Bedrock doesn't have batch API, so we call sequentially.
        Consider rate limiting for large batches.
        """
        embeddings = []
        for text in texts:
            embeddings.append(self.embed(text))
        return embeddings
