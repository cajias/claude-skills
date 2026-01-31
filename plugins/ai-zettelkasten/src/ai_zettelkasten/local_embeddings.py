"""Local embeddings using sentence-transformers."""


class LocalEmbeddings:
    """Generate embeddings locally using sentence-transformers.

    Default model: all-MiniLM-L6-v2 (384 dimensions).
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """Initialize local embeddings with sentence-transformers."""
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415

        self.model = SentenceTransformer(model_name)
        self._dimensions = self.model.get_sentence_embedding_dimension()

    @property
    def dimensions(self) -> int:
        """Return embedding dimensions."""
        return self._dimensions

    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
