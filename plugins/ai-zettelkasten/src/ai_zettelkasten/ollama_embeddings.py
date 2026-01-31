"""Ollama embeddings for local semantic search."""

import httpx


class OllamaEmbeddings:
    """Generate embeddings using a local Ollama instance.

    Default model: nomic-embed-text (768 dimensions).
    """

    def __init__(
        self,
        model_name: str = "nomic-embed-text",
        dimensions: int = 768,
        base_url: str = "http://localhost:11434",
    ) -> None:
        """Initialize Ollama embeddings provider."""
        self.model_name = model_name
        self._dimensions = dimensions
        self.base_url = base_url

    @property
    def dimensions(self) -> int:
        """Return embedding dimensions."""
        return self._dimensions

    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text via Ollama API."""
        response = httpx.post(
            f"{self.base_url}/api/embeddings",
            json={"model": self.model_name, "prompt": text},
        )
        response.raise_for_status()
        return response.json()["embedding"]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        return [self.embed(text) for text in texts]
