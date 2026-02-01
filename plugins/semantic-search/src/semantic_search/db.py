"""LanceDB operations for semantic search."""

from __future__ import annotations

import lancedb
import pyarrow as pa
from sentence_transformers import SentenceTransformer


_model: SentenceTransformer | None = None

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 output dimension


def _get_model() -> SentenceTransformer:
    global _model  # noqa: PLW0603
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def get_table(db_path: str, table_name: str = "notes") -> lancedb.table.Table:
    """Connect to LanceDB and return (or create) the notes table."""
    db = lancedb.connect(db_path)
    try:
        return db.open_table(table_name)
    except Exception:
        schema = pa.schema(
            [
                pa.field("title", pa.utf8()),
                pa.field("content", pa.utf8()),
                pa.field("source", pa.utf8()),
                pa.field("vector", pa.list_(pa.float32(), EMBEDDING_DIM)),
            ],
        )
        return db.create_table(table_name, schema=schema)


def add_documents(table: lancedb.table.Table, docs: list[dict]) -> int:
    """Add documents to the table. Returns count added."""
    model = _get_model()
    embeddings = model.encode([d["content"] for d in docs])
    rows = [
        {
            "title": d["title"],
            "content": d["content"],
            "source": d["source"],
            "vector": emb.tolist(),
        }
        for d, emb in zip(docs, embeddings, strict=True)
    ]
    table.add(rows)
    return len(rows)


def search(table: lancedb.table.Table, query: str, limit: int = 5) -> list[dict]:
    """Search the table, return top results as list of dicts with title, source, score."""
    if table.count_rows() == 0:
        return []
    model = _get_model()
    query_vector = model.encode(query).tolist()
    results = table.search(query_vector).limit(limit).to_list()
    return [{"title": r["title"], "source": r["source"], "score": r["_distance"]} for r in results]
