"""Backend configuration and factory functions."""

import os
from pathlib import Path

from .chromadb_store import ChromaDBStore
from .embeddings import BedrockEmbeddings
from .local_embeddings import LocalEmbeddings
from .ollama_embeddings import OllamaEmbeddings
from .s3vectors import S3VectorsStore


def create_vector_store() -> ChromaDBStore | S3VectorsStore:
    """Create a vector store based on ZETTELKASTEN_BACKEND env var.

    Supported backends:
        - "chromadb" (default): Local ChromaDB with persistent storage
        - "s3": AWS S3 Vectors (requires AWS credentials)
    """
    backend = os.environ.get("ZETTELKASTEN_BACKEND", "chromadb")

    if backend == "chromadb":
        persist_dir = os.environ.get(
            "ZETTELKASTEN_CHROMA_DIR",
            str(Path.home() / ".chroma-data"),
        )
        collection = os.environ.get("ZETTELKASTEN_COLLECTION", "zettelkasten")
        return ChromaDBStore(persist_dir=persist_dir, collection_name=collection)

    if backend == "s3":
        bucket = os.environ.get("ZETTELKASTEN_BUCKET", "zettelkasten-prod")
        index = os.environ.get("ZETTELKASTEN_INDEX", "knowledge-index")
        region = os.environ.get("AWS_REGION", "us-east-1")
        return S3VectorsStore(bucket, index, region)

    msg = f"Unknown backend: {backend}. Use 'chromadb' or 's3'."
    raise ValueError(msg)


def create_embeddings() -> OllamaEmbeddings | BedrockEmbeddings | LocalEmbeddings:
    """Create an embeddings provider based on ZETTELKASTEN_EMBEDDINGS env var.

    Supported providers:
        - "ollama" (default): Local Ollama instance
        - "bedrock": AWS Bedrock Titan
        - "local": sentence-transformers (all-MiniLM-L6-v2)
    """
    provider = os.environ.get("ZETTELKASTEN_EMBEDDINGS", "ollama")

    if provider == "ollama":
        model = os.environ.get("ZETTELKASTEN_OLLAMA_MODEL", "nomic-embed-text")
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        return OllamaEmbeddings(model_name=model, base_url=base_url)

    if provider == "bedrock":
        region = os.environ.get("AWS_REGION", "us-east-1")
        return BedrockEmbeddings(region=region)

    if provider == "local":
        model = os.environ.get("ZETTELKASTEN_LOCAL_MODEL", "all-MiniLM-L6-v2")
        return LocalEmbeddings(model_name=model)

    msg = f"Unknown embeddings: {provider}. Use 'ollama', 'bedrock', or 'local'."
    raise ValueError(msg)
