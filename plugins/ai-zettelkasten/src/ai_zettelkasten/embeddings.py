"""Bedrock Titan embeddings for semantic search."""
import json
from typing import Optional

from .s3vectors import _get_assumed_role_session

# Titan embedding model configuration
TITAN_MODEL_ID = "amazon.titan-embed-text-v1"
TITAN_DIMENSIONS = 1536
TITAN_MAX_INPUT = 8000  # Character limit


class BedrockEmbeddings:
    """Generate embeddings using Bedrock Titan."""

    def __init__(self, region: Optional[str] = None):
        self.model_id = TITAN_MODEL_ID
        self.dimensions = TITAN_DIMENSIONS
        self.max_input = TITAN_MAX_INPUT
        session = _get_assumed_role_session(region or "us-east-1")
        self.client = session.client("bedrock-runtime")

    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        # Truncate if necessary
        truncated = text[:self.max_input]

        response = self.client.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({"inputText": truncated})
        )

        result = json.loads(response["body"].read())
        return result["embedding"]

    def embed_batch(self, texts: list[str], max_workers: int = 10) -> list[list[float]]:
        """Generate embeddings for multiple texts in parallel.

        Uses ThreadPoolExecutor for concurrent API calls since Bedrock
        Titan doesn't have a native batch embedding endpoint.

        Args:
            texts: List of texts to embed
            max_workers: Number of parallel workers (default: 10)

        Returns:
            List of embeddings in the same order as input texts
        """
        from concurrent.futures import ThreadPoolExecutor

        if len(texts) <= 1:
            return [self.embed(text) for text in texts]

        # Use thread pool for parallel API calls
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            embeddings = list(executor.map(self.embed, texts))

        return embeddings
